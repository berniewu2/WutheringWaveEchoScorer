from paddleocr import PaddleOCR

from utils import *
from resonator import *
from data import *


def process_image(path):
    src_path = Path(path)
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

    for _ in range(5):
        for i in range(5):
            echo_list[i].add_property(
                Property(
                    {"property": clean_ocr_minor_key(sub_data[i * 2]), "value": clean_ocr_value(sub_data[i * 2 + 1])}
                )
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
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    out_path = output_dir / f"{resonator.name}_score.jpg"  
    draw_resonator_stats(
        background_path=src_path,
        output_path=str(out_path),
        resonator=resonator,
    )


if __name__ == "__main__":
    input_dir = Path("input")
    image_exts = {".png", ".jpg", ".jpeg"}

    if not input_dir.exists():
        print(f"Input directory {input_dir!r} does not exist.")
    else:
        image_files = [p for p in input_dir.iterdir() if p.suffix.lower() in image_exts]

        if not image_files:
            print(f"No image files found in {input_dir!r}.")
        else:
            for img_path in image_files:
                print(f"Processing {img_path!r} …")
                process_image(img_path)
