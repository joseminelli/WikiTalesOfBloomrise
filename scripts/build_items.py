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
    "all_recipes": ("recipes.md", "Livro de Receitas Completo"),
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

REAL_FILENAME_MAP = {}

def map_real_filenames():
    """Mapeia nomes de arquivos reais indexando-os por versões normalizadas."""
    global REAL_FILENAME_MAP
    if ASSETS_DIR.exists():
        for file in ASSETS_DIR.iterdir():
            if file.is_file():
                # CHAVE 1: Tudo colado e minúsculo (ex: batataassada)
                clean_key = file.stem.lower().replace("-", "").replace("_", "")
                REAL_FILENAME_MAP[clean_key] = file.name
                
                # CHAVE 2: Slug padrão (ex: batata-assada)
                slug_key = slug(file.stem)
                REAL_FILENAME_MAP[slug_key] = file.name

def resolve_item_icon(item_id):
    if not REAL_FILENAME_MAP:
        map_real_filenames()
    
    # 1. Tenta slug (batata-assada)
    target_slug = slug(item_id)
    if target_slug in REAL_FILENAME_MAP:
        return REAL_FILENAME_MAP[target_slug]
        
    # 2. Tenta tudo colado (batataassada)
    target_clean = item_id.lower().replace("-", "").replace("_", "")
    if target_clean in REAL_FILENAME_MAP:
        return REAL_FILENAME_MAP[target_clean]
    
    # 3. Tenta ID bruto minúsculo
    if item_id.lower() in REAL_FILENAME_MAP:
        return REAL_FILENAME_MAP[item_id.lower()]

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

def get_how_to_obtain(item, item_id, recipes, used_in):
    # 1. Crafting (Prioridade alta: se tem receita, é fabricável)
    if item_id in recipes:
        return "🔨 <strong>Crafting:</strong> Este item pode ser fabricado em uma bancada ou forja utilizando os materiais necessários."

    # 2. Drops de Monstros (Baseado em palavras-chave comuns de loot)
    monster_keywords = ["fang", "fantasma", "veneno", "slime", "morcego", "bone", "rat", "zombie"]
    if any(key in item_id.lower() for key in monster_keywords):
        return "⚔️ <strong>Combate:</strong> Dropado por criaturas ao derrotá-las em combate nas dungeons ou arredores da vila."

    # 3. Flores e Plantas Silvestres (Coleta vs Cultivo)
    i_type = item.get("itemType", "")
    if i_type == "Flower":
        return "🌸 <strong>Coleta:</strong> Cresce naturalmente pelo mundo. Pode ser colhida durante as estações corretas."
    
    if "seed" in item_id.lower():
        return "📦 <strong>Comércio:</strong> Geralmente comprada na Loja de flores perto da casa do Lupi ou encontrada explorando."
    
    if i_type == "Plant":
        return "🌱 <strong>Cultivo:</strong> Deve ser plantado a partir de sementes e colhido na fazenda após o tempo de crescimento."

    plant_keywords = ["abobora", "wheat", "batata", "cebola", "cenoura", "corn", "grape", "strawberry", "turnip", "tomato"]
    if any(key in item_id.lower() for key in plant_keywords):
        return "🌱 <strong>Cultivo:</strong> Deve ser plantado a partir de sementes e colhido na fazenda após o tempo de crescimento."
    # 4. Mineração
    mining_keywords = ["ore", "pedra", "carvao", "iron", "gold", "crystal", "copper", "diamante", "chromita", "Diamante", "esmeralma", "ametista"]
    if any(key in item_id.lower() for key in mining_keywords):
        return "⛏️ <strong>Mineração:</strong> Extraído de rochas e veios de minério dentro das cavernas ou ruínas."

    fishing_keywords = ["herring", "chub", "rainbowtr", "sardinha", "tilapia"]
    if any(key in item_id.lower() for key in fishing_keywords):
        return "🎣 <strong>Pesca:</strong> Pode ser pescado em rios, lagos e mares com uma vara de pesca."

    # Fallback
    return "🌍 <strong>Exploração:</strong> Pode ser encontrado em baús, quebrando barris, como recompensa de moradores ou comprando em lojas."

# ========================
# Page builders
# ========================

def build_recipes_page(items, locale, recipes, item_map):
    path = DOCS_DIR / "recipes.md"
    
    recipes_by_cat = {}
    for res_id, recipe in recipes.items():
        res_item = item_map.get(res_id.lower())
        if not res_item: continue
        cat = detect_category(res_item)
        if cat not in recipes_by_cat: recipes_by_cat[cat] = []
        recipes_by_cat[cat].append((res_id, recipe))

    with open(path, "w", encoding="utf-8") as md:
        # Front matter para garantir que o título não duplique
        md.write("---\ntitle: Livro de Receitas\n---\n\n")
        
        md.write("# 📖 Livro de Receitas\n\n")
        
        # --- NOVO: Botões de Filtro ---
        md.write('<div class="recipe-filters">\n')
        md.write('  <button class="filter-btn active" onclick="filterRecipes(\'all\')">Tudo</button>\n')
        md.write('  <button class="filter-btn" onclick="filterRecipes(\'consumables_hp\')">Culinária (HP)</button>\n')
        md.write('  <button class="filter-btn" onclick="filterRecipes(\'consumables_energy\')">Culinária (Energia)</button>\n')
        md.write('  <button class="filter-btn" onclick="filterRecipes(\'equipment\')">Equipamentos</button>\n')
        md.write('  <button class="filter-btn" onclick="filterRecipes(\'materials\')">Materiais</button>\n')
        md.write('</div>\n\n')

        # Container principal das receitas
        md.write('<div id="recipes-master-list">\n')

        priority = ["consumables_hp", "consumables_energy", "materials", "equipment", "placeable"]
        sorted_cats = sorted(recipes_by_cat.keys(), key=lambda x: priority.index(x) if x in priority else 99)

        for cat in sorted_cats:
            # Envolvemos cada categoria em uma div com classe para o filtro
            md.write(f'<div class="recipe-category-section" data-cat="{cat}">\n')
            md.write(f"<h2> {getCategoryTitle(cat)}\n</h2>\n")
            md.write('<div class="recipes-container">\n')
            
            current_recipes = sorted(recipes_by_cat[cat], key=lambda x: t(locale, item_map.get(x[0].lower(), {}).get("nameKey"), x[0]))

            for res_id, recipe in current_recipes:
                res_item = item_map.get(res_id.lower())
                res_name = t(locale, res_item.get("nameKey"), res_id)
                res_link = f"./{cat}/_items/{slug(res_id)}/"
                icon_res = resolve_item_icon(res_id)

                md.write(f'''
<div class="recipe-card-full" data-category="{cat}">
    <div class="recipe-header">
        <img src="{ICON_PATH}/{icon_res}" class="mini-icon">
        <strong><a href="../{res_link}">{res_name}</a></strong>
        <span class="yield-badge">x{recipe["yield"]}</span>
    </div>
    <div class="recipe-ingredients-list">''')
                
                for ing in recipe["ingredients"]:
                    ing_id = ing["id"]
                    ing_item = item_map.get(ing_id.lower())
                    ing_name = t(locale, ing_item.get("nameKey"), ing_id) if ing_item else ing_id
                    icon_ing = resolve_item_icon(ing_id)
                    
                    md.write(f'''
        <div class="ing-item" title="{ing_name}">
            <img src="{ICON_PATH}/{icon_ing}">
            <span>{ing["qty"]}</span>
        </div>''')

                md.write('\n    </div>\n</div>')
            
            md.write('\n</div>\n</div>\n') # Fecha recipes-container e recipe-category-section
            
        md.write('\n</div>\n') # Fecha recipes-master-list

        # --- NOVO: Script de Filtro ---
        md.write('''
<script>
function filterRecipes(cat) {
    const sections = document.querySelectorAll('.recipe-category-section');
    const buttons = document.querySelectorAll('.filter-btn');
    
    buttons.forEach(btn => btn.classList.remove('active'));
    event.currentTarget.classList.add('active');

    sections.forEach(section => {
        if (cat === 'all' || section.getAttribute('data-cat') === cat) {
            section.style.display = 'block';
        } else {
            section.style.display = 'none';
        }
    });
}
</script>
''')

def write_item_page(item, locale, category, recipes, used_in, item_map):
    item_id = item["id"]
    category_dir = DOCS_DIR / category / "_items"
    category_dir.mkdir(parents=True, exist_ok=True)

    page = category_dir / f"{slug(item_id)}.md"
    name = t(locale, item.get("nameKey"), item_id.replace("_", " "))
    description = t(locale, item.get("descriptionKey"), "")
    icon = resolve_item_icon(item_id)
    obtain_method = get_how_to_obtain(item, item_id, recipes, used_in)

    with open(page, "w", encoding="utf-8") as md:
        md.write(f"---\ntitle: \"{name}\"\n---\n\n")
        md.write(f"<div class=\"item-page\">\n")
        
        # Header com visual de Badge
        md.write(f"<div class=\"item-header\">\n   <img src=\"{ICON_PATH}/{icon}\" class=\"item-icon\" alt=\"{name}\">\n")
        md.write(f"   <div class=\"item-info\">\n     <h1 class=\"item-title\">{name}</h1>\n     <span class=\"item-category\" data-category=\"{category}\">{getCategoryTitle(category)}</span>\n   </div>\n</div>\n\n")
        
        # Seção de Descrição e Obtenção lado a lado (estilo RPG)
        md.write(f"<div class=\"item-section\">\n  <div class=\"flavor-text\">\n    <span class=\"icon-label\">📝 Descrição</span>\n    <p>{description or 'Um item misterioso encontrado em Bloomrise.'}</p>\n  </div>\n</div><br>\n\n")
        
        md.write(f"<div class=\"item-section\">\n  <div class=\"obtain-box\">\n    <span class=\"icon-label\">📍 Como Obter</span>\n    <div class=\"obtain-content\">{obtain_method}</div>\n  </div>\n</div>\n\n")

        # Efeitos com visual de Atributos
        effects = []
        if item.get("healthValue", 0) > 0: effects.append(f"❤️ **Vida:** +{item['healthValue']}")
        if item.get("staminaValue", 0) > 0: effects.append(f"⚡ **Energia:** +{item['staminaValue']}")
        if effects:
            md.write('<div class="item-section"><h3>✨ Atributos</h3><div class="effects-grid">')
            for e in effects: md.write(f"<div class='effect-tag'>{e}</div>")
            md.write("</div></div>\n")

        # Crafting (Como Criar)
        # Verificação case-insensitive da receita
        # Crafting (Como Criar) - Versão Mini-Cards
        recipe = recipes.get(item_id)
        if recipe:
            md.write('<div class="item-section">')
            md.write('<h2>🔨 Como Criar</h2>')
            md.write(f'<p class="yield-text" style="margin-bottom: 0.5rem; font-size: 0.9rem; opacity: 0.8;">Rende: <strong>{recipe["yield"]}x</strong></p>')
            md.write('<div class="used-grid">') # Reutiliza sua classe de grid flexível
            
            for ing in recipe["ingredients"]:
                ing_id_raw = ing["id"]
                ing_item = item_map.get(ing_id_raw.lower())
                ing_name = t(locale, ing_item.get("nameKey"), ing_id_raw) if ing_item else ing_id_raw.replace("_", " ").title()
                icon_ing = resolve_item_icon(ing_id_raw)
                
                # Texto formatado: "2x Presa de Goblin"
                display_text = f"{ing['qty']}x {ing_name}"
                
                if ing_item:
                    ing_cat = detect_category(ing_item)
                    # Caminho relativo para o link do ingrediente
                    ing_link = f"/items/{ing_cat}/_items/{slug(ing_id_raw)}/"
                    
                    md.write(f'''
    <a href="{ing_link}" class="mini-card">
        <img src="{ICON_PATH}/{icon_ing}" alt="{ing_name}">
        <span>{display_text}</span>
    </a>''')
                else:
                    # Caso o ingrediente não seja um item catalogado (apenas texto)
                    md.write(f'''
    <div class="mini-card">
        <img src="{ICON_PATH}/{icon_ing}" alt="{ing_name}">
        <span>{display_text}</span>
    </div>''')
            
            md.write('</div></div>')

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
    map_real_filenames()
    items = load_items()
    locale = load_locale()
    recipes, used_in = load_recipes()
    build_tables(items, locale, recipes, used_in)
    build_recipes_page(items, locale, recipes, {item["id"].lower(): item for item in items})
    print("✅ Todas as páginas de itens foram geradas com sucesso!")