import json
import csv
import re
import unicodedata
from pathlib import Path

# ========================
# Paths
# ========================
DATA_FILE = Path("data/items.json")
LOCALE_FILE = Path("data/pt_BR.csv")
RECIPES_FILE = Path("data/Export_Recipes.csv")

DOCS_DIR = Path("docs/items")
ASSETS_DIR = Path("docs/assets/items") # Onde as imagens estão fisicamente
# No MkDocs, se assets está na raiz de docs, o caminho no navegador é /assets/items/
ICON_PATH = "/assets/items"
PLACEHOLDER_IMAGE = "placeholder.png"

FILES = {
    "materials": ("materials.md", "Materiais e Itens Gerais"),
    "consumables_hp": ("consumables_hp.md", "Consumíveis — Vida"),
    "consumables_energy": ("consumables_energy.md", "Consumíveis — Energia"),
    "equipment": ("equipment.md", "Equipamentos"),
    "placeable": ("placeable.md", "Itens Posicionáveis"),
    "books": ("books.md", "Livros e Guias"),  # Nova categoria
    "plants": ("plants.md", "Plantas e Flores"), # Nova categoria
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
        next(reader)
        for row in reader:
            if not row: continue
            key = row[0].strip()
            text = ";".join(row[1:]).strip()
            if key: locale[key] = text
    return locale

def load_recipes():
    recipes = {}
    used_in = {}
    
    if not RECIPES_FILE.exists():
        print(f"⚠ Aviso: Arquivo de receitas não encontrado em {RECIPES_FILE}")
        return {}, {}

    with open(RECIPES_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=',') 
        
        for row in reader:
            row = {k.strip(): v for k, v in row.items() if k}
            res_id_raw = row.get('Item Criado (ID)')
            if not res_id_raw: continue
            
            res_id = res_id_raw.strip()
            ingredients = []
            
            for i in range(1, 6):
                ing_id = row.get(f'Ingrediente {i} (ID)')
                qty = row.get(f'Qtd {i}')
                
                if ing_id and str(ing_id).lower() != "none" and qty:
                    try:
                        ing_id = ing_id.strip()
                        q_val = int(float(qty))
                        ingredients.append({"id": ing_id, "qty": q_val})
                        
                        # Mapeia quem usa este ingrediente (Case Insensitive)
                        ing_key = ing_id.lower()
                        if ing_key not in used_in: used_in[ing_key] = []
                        if res_id not in used_in[ing_key]: used_in[ing_key].append(res_id)
                    except: continue
            
            try: yield_qty = int(float(row.get('Quantidade', 1)))
            except: yield_qty = 1

            # Armazena a receita usando o ID original do CSV
            recipes[res_id] = {"yield": yield_qty, "ingredients": ingredients}
            
    return recipes, used_in

# ========================
# Helpers
# ========================
def t(locale, key, fallback=""):
    if not key: return fallback
    return locale.get(key, fallback or key)

def resolve_item_icon(item_id):
    # Força o nome do arquivo a ser o slug. Ex: "Wood Axe" -> "wood-axe.png"
    icon_file = f"{slug(item_id)}.png"
    if (ASSETS_DIR / icon_file).exists():
        return icon_file
    return PLACEHOLDER_IMAGE

def detect_category(item):
    i_type = item.get("itemType", "")
    item_id = item.get("id", "").lower()

    # 1. Prioridade para Livros
    if i_type in ["LoreBook", "Guidebook"]:
        return "books"

    # 2. Prioridade para Plantas e Sementes
    # Adicionei uma verificação extra caso o ID contenha "seed" 
    if i_type in ["Flower", "Plant"] or "seed" in item_id:
        return "plants"
    if i_type == "Placeable":
        return "placeable"

    # 3. Consumíveis (Food)
    # Verificamos se restaura algo ou se é do tipo Food
    if i_type == "Food" or item.get("isConsumable"):
        if item.get("healthValue", 0) > 0: 
            return "consumables_hp"
        if item.get("staminaValue", 0) > 0: 
            return "consumables_energy"

    # 4. Equipamentos (Só entra aqui se não for planta/comida/livro)
    # Verificamos weaponId e toolType, mas ignoramos se for "None"
    has_weapon = item.get("weaponId") and item.get("weaponId") != ""
    has_tool = item.get("toolType") not in ["None", "", None]
    
    if i_type == "Weapon" or has_weapon or has_tool:
        return "equipment"

    # 5. Fallback para materiais
    return "materials"

def getCategoryTitle(category):
    return FILES.get(category, ("", "Categoria Desconhecida"))[1]

def slug(text: str):
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")

# ========================
# Page builders
# ========================
def write_item_page(item, locale, category, recipes, used_in, item_map):
    item_id = item["id"]
    category_dir = DOCS_DIR / category / "_items"
    category_dir.mkdir(parents=True, exist_ok=True)

    page = category_dir / f"{slug(item_id)}.md"
    name = t(locale, item.get("nameKey"), item_id.replace("_", " "))
    description = t(locale, item.get("descriptionKey"), "")
    icon = resolve_item_icon(item_id)

    with open(page, "w", encoding="utf-8") as md:
        md.write(f"---\ntitle: {name}\n---\n\n<div class=\"item-page\">\n")
        md.write(f"<div class=\"item-header\">\n  <img src=\"{ICON_PATH}/{icon}\" class=\"item-icon\" alt=\"{name}\">\n")
        md.write(f"  <div class=\"item-info\">\n    <h1>{name}</h1>\n    <span class=\"item-category\">{getCategoryTitle(category)}</span>\n  </div>\n</div>\n")
        md.write(f"<div class=\"item-section\"><h2>📝 Descrição</h2><p>{description or 'Sem descrição disponível.'}</p></div>\n")
        
        # Efeitos
        effects = []
        if item.get("healthValue", 0) > 0: effects.append(f"❤️ Vida +{item['healthValue']}")
        if item.get("staminaValue", 0) > 0: effects.append(f"⚡ Energia +{item['staminaValue']}")
        if effects:
            md.write('<div class="item-section"><h2>✨ Efeitos</h2><ul>')
            for e in effects: md.write(f"<li>{e}</li>")
            md.write("</ul></div>")

        # Crafting (Como Criar)
        # Verificação case-insensitive da receita
        recipe = recipes.get(item_id)
        if recipe:
            md.write('<div class="item-section crafting"><h2>🔨 Como Criar</h2><div class="recipe-box">')
            md.write(f'<p>Rende: <strong>{recipe["yield"]}x</strong></p><ul>')
            for ing in recipe["ingredients"]:
                ing_id_raw = ing["id"]
                ing_item = item_map.get(ing_id_raw.lower())
                ing_name = t(locale, ing_item.get("nameKey"), ing_id_raw) if ing_item else ing_id_raw.replace("_", " ").title()
                
                if ing_item:
                    ing_cat = detect_category(ing_item)
                    ing_link = f"/items/{ing_cat}/_items/{slug(ing_id_raw)}/"
                    md.write(f'<li><img src="{ICON_PATH}/{resolve_item_icon(ing_id_raw)}" class="mini-icon"> {ing["qty"]}x <a href="{ing_link}">{ing_name}</a></li>')
                else:
                    md.write(f'<li><img src="{ICON_PATH}/{resolve_item_icon(ing_id_raw)}" class="mini-icon"> {ing["qty"]}x {ing_name}</li>')
            md.write("</ul></div></div>")

        # Usado em
        used_list = used_in.get(item_id.lower())
        if used_list:
            md.write('<div class="item-section used-in"><h2>🛠️ Usado para criar</h2><div class="used-grid">')
            for res_id in used_list:
                res_item = item_map.get(res_id.lower())
                res_name = t(locale, res_item.get("nameKey"), res_id) if res_item else res_id.replace("_", " ").title()
                
                if res_item:
                    res_cat = detect_category(res_item)
                    res_link = f"/items/{res_cat}/_items/{slug(res_id)}/"
                    md.write(f'<a href="{res_link}" class="mini-card"><img src="{ICON_PATH}/{resolve_item_icon(res_id)}"><span>{res_name}</span></a>')
                else:
                    md.write(f'<div class="mini-card"><img src="{ICON_PATH}/{resolve_item_icon(res_id)}"><span>{res_name}</span></div>')
            md.write("</div></div>")

        md.write("</div>")

def build_tables(items, locale, recipes, used_in):
    item_map = {item["id"].lower(): item for item in items}
    
    grouped = {key: [] for key in FILES.keys()}
    for item in items:
        category = detect_category(item)
        grouped[category].append(item)
        write_item_page(item, locale, category, recipes, used_in, item_map)

    for category, (filename, title) in FILES.items():
        path = DOCS_DIR / filename
        with open(path, "w", encoding="utf-8") as md:
            md.write(f"# {title}\n\n<div class=\"items-grid\">\n")
            for item in grouped[category]:
                name = t(locale, item.get("nameKey"), item["id"].replace("_", " "))
                desc_text = t(locale, item.get("descriptionKey"), "")
                desc = (desc_text[:77] + "...") if len(desc_text) > 80 else desc_text
                icon = resolve_item_icon(item["id"])
                link = f"./_items/{slug(item['id'])}"
                md.write(f'<a class="item-card" href="{link}"><img src="{ICON_PATH}/{icon}"><div><strong>{name}</strong><p>{desc}</p></div></a>\n')
            md.write('</div>\n')
        print(f"✔ Gerado: {path}")

if __name__ == "__main__":
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    
    items = load_items()
    locale = load_locale()
    recipes, used_in = load_recipes()
    build_tables(items, locale, recipes, used_in)