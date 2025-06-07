from difflib import get_close_matches
import re
from pathlib import Path
import cv2
from data import (
    damage_composition,
    multiplier_weights,
    VALID_MINOR_PROPERTY,
    VALID_MAJOR_PROPERTY,
)
from resonator import Echo


def load_image(path: Path) -> cv2.Mat:
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"Could not load image at {path!r}")
    return img


def normalize_name(raw: str) -> str:

    s = raw.strip().lower()

    if s.startswith("the "):
        s = s[4:].strip()

    s = re.sub(r"[^a-z ]", "", s)

    for key in damage_composition.keys():
        if s == key.lower():
            return key

    all_keys_lower = [k.lower() for k in damage_composition.keys()]
    close = get_close_matches(s, all_keys_lower, n=1, cutoff=0.6)
    if close:
        # find which original key corresponds to that lowercase match
        matched_lower = close[0]
        idx = all_keys_lower.index(matched_lower)
        return list(damage_composition.keys())[idx]
    return ""


def clean_ocr_major_key(raw: str) -> str:
    _SIMPLIFIED_TO_CANON = {re.sub(r"[^a-z0-9]", "", key.lower()): key for key in VALID_MAJOR_PROPERTY}

    s = re.sub(r"^[\+\-]+", "", raw.strip())
    s = re.sub(r"\s+", " ", s)
    for key in VALID_MAJOR_PROPERTY:
        if s.lower() == key.lower():
            return key
    simplified = re.sub(r"[^a-z0-9]", "", s.lower())
    return _SIMPLIFIED_TO_CANON.get(simplified, "")


def clean_ocr_minor_key(raw: str) -> str:

    _SIMPLIFIED_TO_CANON = {re.sub(r"[^a-z0-9]", "", key.lower()): key for key in VALID_MINOR_PROPERTY}
    if not isinstance(raw, str):
        return ""

    s = re.sub(r"^[\+\-]+", "", raw.strip())

    s = re.sub(r"\s+", " ", s)

    for key in VALID_MINOR_PROPERTY:
        if s.lower() == key.lower():
            return key

    simplified = re.sub(r"[^a-z0-9]", "", s.lower())
    return _SIMPLIFIED_TO_CANON.get(simplified, "")


def clean_ocr_sub_key(s: str) -> str:
    tmp = s.upper().strip()
    m = re.search(r"(ATK|HP)", tmp)
    return m.group(1) if m else ""


def clean_ocr_value(s: str) -> str:
    s = re.sub(r"[^\d\.%]", "", s)
    if s[-1] == "%" and "." not in s:
        if len(s) > 3:
            s = s[-3:]
    return s


def build_weight(char):
    category = damage_composition[char]["composition"]["type"]
    weight = {}
    for key, value in multiplier_weights[category].items():
        if key != "Special Damage":
            weight[key] = value
        else:
            for k, v in damage_composition[char]["composition"].items():
                weight[k] = v
    return weight


damege_types = ["Basic Attack", "Resonance Skill", "Resonance Liberation", "Heavy Attack"]
elemental_types = [
    "Electro DMG Bonus",
    "Glacio DMG Bonus",
    "Fusion DMG Bonus",
    "Aero DMG Bonus",
    "Spectro DMG Bonus",
    "Havoc DMG Bonus",
]


def calculate_property_score(attribute: dict, weight: dict):
    property = attribute["property"]
    for damege_type in damege_types:
        if damege_type in property:
            property = damege_type
    if any(e in property for e in elemental_types):
        property = "Elemental Damage Bonus"
    if "%" in attribute["value"]:
        value = float(attribute["value"].replace("%", ""))
        if len(attribute["property"]) <= 3:
            property = attribute["property"] + "%"
    else:
        value = float(attribute["value"])
    if property == "Energy Regen":
        return 100.0 * (weight["Energy Regen"][1] * min(value, weight["Energy Regen"][0]))
    return 100.0 * weight.get(property, 0) * value


def calculate_echo_score(echo: Echo, weight: dict, perfect_score: float):
    attribute_score = calculate_property_score(echo.main_attribute, weight) / perfect_score
    energy_regen = (
        float(echo.main_attribute.get("value")[:-1])
        if echo.main_attribute.get("property") == "Energy Regen"
        else 0
    )
    echo_score = attribute_score
    attribute_score = calculate_property_score(echo.sub_attribute, weight) / perfect_score
    energy_regen += (
        float(echo.sub_attribute.get("value")[:-1])
        if echo.sub_attribute.get("property") == "Energy Regen"
        else 0
    )
    echo_score += attribute_score
    for property in echo.property_list:
        attribute_score = calculate_property_score(property, weight) / perfect_score
        energy_regen += float(property.get("value")[:-1]) if property.get("property") == "Energy Regen" else 0
        echo_score += attribute_score
    return echo_score, energy_regen
