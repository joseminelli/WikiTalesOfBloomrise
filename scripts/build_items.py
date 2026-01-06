import json
import csv
from pathlib import Path

# ========================
# Paths
# ========================
DATA_FILE = Path("data/items.json")
LOCALE_FILE = Path("data/pt_BR.csv")

DOCS_DIR = Path("docs/items")
ITEM_PAGES_DIR = DOCS_DIR / "_items"

ASSETS_DIR = Path("docs/assets/items")
ICON_PATH = "../../assets/items"
PLACEHOLDER_IMAGE = "placeholder.png"

FILES = {
    "materials": ("materials.md", "Materiais e Itens Gerais"),
    "consumable_hp": ("consumables_hp.md", "Consumíveis — Vida"),
    "consumable_energy": ("consumables_energy.md", "Consumíveis — Energia"),
    "equipment": ("equipment.md", "Equipamentos"),
}

# ========================
# Loaders
# ========================
def load_items():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)["list"]

def load_locale():
    locale = {}
    with open(LOCALE_FILE, encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=";")
        next(reader)  # pula header

        for row in reader:
            if not row:
                continue

            key = row[0].strip()
            text = ";".join(row[1:]).strip()

            if key:
                locale[key] = text

    return locale


# ========================
# Helpers
# ========================
def t(locale, key, fallback=""):
    if not key:
        return fallback
    return locale.get(key, fallback or key)

def resolve_item_icon(item_id):
    icon_file = f"{item_id.lower()}.png"
    if (ASSETS_DIR / icon_file).exists():
        return icon_file
    return PLACEHOLDER_IMAGE

def detect_category(item):
    if item.get("toolType") != "None" or item.get("weaponId"):
        return "equipment"

    if item.get("isConsumable"):
        if item.get("healthValue", 0) > 0:
            return "consumable_hp"
        if item.get("staminaValue", 0) > 0:
            return "consumable_energy"

    return "materials"

def slug(item_id):
    return item_id.lower().replace("_", "")

# ========================
# Page builders
# ========================
def write_item_page(item, locale):
    item_id = item["id"]
    page = ITEM_PAGES_DIR / f"{slug(item_id)}.md"

    name = t(locale, item.get("nameKey"), item_id.replace("_", " "))
    description = t(locale, item.get("descriptionKey"), "")

    effects = []
    if item.get("healthValue", 0) > 0:
        effects.append(f"- ❤️ Vida: +{item['healthValue']}")
    if item.get("staminaValue", 0) > 0:
        effects.append(f"- ⚡ Energia: +{item['staminaValue']}")

    icon = resolve_item_icon(item_id)

    with open(page, "w", encoding="utf-8") as md:
        md.write(f"# {name}\n\n")
        md.write(f"![{name}]({ICON_PATH}/{icon})\n\n")

        md.write("## Descrição\n")
        md.write(f"{description}\n\n")

        if effects:
            md.write("## Efeitos\n")
            md.write("\n".join(effects) + "\n")

def build_tables(items, locale):
    grouped = {key: [] for key in FILES.keys()}

    for item in items:
        category = detect_category(item)
        grouped[category].append(item)
        write_item_page(item, locale)

    for category, (filename, title) in FILES.items():
        path = DOCS_DIR / filename
        with open(path, "w", encoding="utf-8") as md:
            md.write(f"# {title}\n\n")
            md.write("| Item | Descrição |\n")
            md.write("|------|-----------|\n")

            for item in grouped[category]:
                name = t(locale, item.get("nameKey"), item["id"].replace("_", " "))
                desc = t(locale, item.get("descriptionKey"), "")
                link = f"./_items/{slug(item['id'])}.md"

                md.write(f"| **[{name}]({link})** | {desc} |\n")

        print(f"✔ Gerado: {path}")

# ========================
# Main
# ========================
if __name__ == "__main__":
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    ITEM_PAGES_DIR.mkdir(parents=True, exist_ok=True)

    items = load_items()
    locale = load_locale()

    build_tables(items, locale)
