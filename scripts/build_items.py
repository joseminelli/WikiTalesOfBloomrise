import json
from pathlib import Path

DATA_FILE = Path("data/items.json")
OUTPUT_DIR = Path("docs/items")
ICON_PATH = "../assets/items"

FILES = {
    "materials": ("materials.md", "Materiais e Itens Gerais"),
    "consumable_hp": ("consumables_hp.md", "Consumíveis — Vida"),
    "consumable_energy": ("consumables_energy.md", "Consumíveis — Energia"),
    "equipment": ("equipment.md", "Equipamentos"),
}

def load_items():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    # Seu JSON tem uma chave "list"
    return data["list"]

def detect_category(item):
    if item.get("toolType") != "None" or item.get("weaponId"):
        return "equipment"

    if item.get("isConsumable"):
        if item.get("healthValue", 0) > 0:
            return "consumable_hp"
        if item.get("staminaValue", 0) > 0:
            return "consumable_energy"

    return "materials"

def build_tables(items):
    grouped = {key: [] for key in FILES.keys()}

    for item in items:
        category = detect_category(item)
        grouped[category].append(item)

    for category, (filename, title) in FILES.items():
        path = OUTPUT_DIR / filename
        with open(path, "w", encoding="utf-8") as md:
            md.write(f"# {title}\n\n")
            md.write("| Item | Descrição |\n")
            md.write("|------|-----------|\n")

            for item in grouped[category]:
                name = item["id"].replace("_", " ")
                desc = f"_{item['descriptionKey']}_"

                md.write(f"| **{name}** | {desc} |\n")

        print(f"✔ Gerado: {path}")

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    items = load_items()
    build_tables(items)
