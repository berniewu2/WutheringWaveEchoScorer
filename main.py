from paddleocr import PaddleOCR

from utils import *
from resonator import *
from data import *

src_path = Path("resonator.jpeg")
img = load_image(src_path)
h, w, _ = img.shape
char_box = {"name": "character_info", "coords": (0, 0, 650, 600)}
resonance_box = {"name": "resonance_tree", "coords": (780, 50, 1400, 620)}
weapon_box = {"name": "equipped_weapon", "coords": (1400, 400, 1800, 650)}
echos_box = {"name": "echos_row", "coords": (0, 650, 1920, 1080)}
boxes = [char_box, resonance_box, weapon_box, echos_box]

Path("crops").mkdir(exist_ok=True)
for box in boxes:
    x1, y1, x2, y2 = box["coords"]
    cropped = img[y1:y2, x1:x2]
    out_path = Path("crops") / f"{box['name']}.png"
    cv2.imwrite(str(out_path), cropped)
    print(f"Saved '{box['name']}' → {out_path}")


ocr = PaddleOCR(use_doc_orientation_classify=False, use_doc_unwarping=False, use_textline_orientation=False)

raw_ocr_character = ocr.predict(input="crops/character_info.png")
ocr_result = dict(raw_ocr_character[0])
data = [i for i in ocr_result.get("rec_texts") if len(i) > 1]
charcter_name = normalize_name(data[0])

raw_ocr_echos = ocr.predict(input="crops/echos_row.png")
ocr_result = dict(raw_ocr_echos[0])
data = [i for i in ocr_result.get("rec_texts") if len(i) > 1]
data = [i for i in data if i != "Bonus" and i != "DMG Bonus" and i != "DMGBonus"]

echo_list = []
for i in range(5):
    property = clean_ocr_major_key(data[i])
    cost = 1
    if property in VALID_MAJOR_PROPERTY:
        cost = 4
    elif property in VALID_MINOR_PROPERTY:
        cost = 3
    echo_list.append(
        EchoBuilder()
        .set_main_attribute(Property({"property": property, "value": clean_ocr_value(data[i + 5])}))
        .set_cost(cost)
    )

sub_data = data[10:]

for i in range(5):
    echo_list[i].set_sub_attributes(
        Property({"property": clean_ocr_sub_key(sub_data[i * 2]), "value": clean_ocr_value(sub_data[i * 2 + 1])})
    )
sub_data = sub_data[10:]

for j in range(5):
    for i in range(5):
        echo_list[i].add_property(
            Property({"property": clean_ocr_minor_key(sub_data[i * 2]), "value": clean_ocr_value(sub_data[i * 2 + 1])})
        )

    sub_data = sub_data[10:]

echo_list = [i.build() for i in echo_list]

weight = build_weight(charcter_name)

resonator = Resonator(charcter_name, echo_list)
resonator.set_weight(weight)

for i in echo_list:
    echo_score, energy_regen = calculate_echo_score(i, resonator.weight, resonator.perfect_score)
    i.set_score(echo_score)
    resonator.add_energy_regen(energy_regen)

resonator.set_score()
print("=" * 50)
print(resonator)
print("=" * 50)


draw_resonator_stats(
    background_path="resonator.jpeg",
    output_path="resonator_score.png",
    resonator=resonator,
)
