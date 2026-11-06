import itemsJson from '../data/items.json';
import recipesJson from '../data/recipes.json';
import plantsJson from '../data/plants.json';
import monstersJson from '../data/monsters.json';
import npcsJson from '../data/npcs.json';
import questsJson from '../data/quests.json';
import skillsJson from '../data/skills.json';
import guideJson from '../data/guide.json';
import shopsJson from '../data/shops.json';
import petsJson from '../data/pets.json';
import lootTablesJson from '../data/lootTables.json';
import spoilersJson from '../data/spoilers.json';
import areasJson from '../data/areas.json';
import { LANGS, type Lang } from './i18n';

export const items = itemsJson as any[];
export const recipes = recipesJson as any[];
export const plants = plantsJson as any[];
export const monsters = monstersJson as any[];
export const npcs = npcsJson as any[];
export const quests = questsJson as any[];
export const skills = skillsJson as any[];
export const guide = guideJson as any[];
export const shops = shopsJson as any[];
export const pets = petsJson as any[];
export const lootTables = lootTablesJson as any[];

const texts = import.meta.glob('../data/i18n/*.json', { eager: true, import: 'default' }) as Record<string, Record<string, string>>;
const dict: Record<string, Record<string, string>> = {};
for (const [p, v] of Object.entries(texts)) dict[p.split('/').pop()!.replace('.json', '')] = v;

/** Texto do jogo por chave, com fallback idioma -> en_US -> pt_BR -> fallback. */
export function g(lang: Lang, key: string | undefined, fallback = ''): string {
  if (!key) return fallback;
  return dict[lang.code]?.[key] || dict['en_US']?.[key] || dict['pt_BR']?.[key] || fallback || key;
}

export const itemById = new Map(items.map((i) => [i.id, i]));
export const recipeById = new Map(recipes.map((r) => [r.id, r]));
export const monsterById = new Map(monsters.map((m) => [m.id, m]));
export const npcById = new Map(npcs.map((n) => [n.id, n]));
export const questById = new Map(quests.map((q) => [q.id, q]));
export const skillById = new Map(skills.map((s) => [s.id, s]));
export const plantById = new Map(plants.map((p) => [p.id, p]));

export const itemName = (lang: Lang, it: any) => g(lang, it?.nameKey, it?.fallbackName ?? it?.id ?? '?');
export const itemDesc = (lang: Lang, it: any) => g(lang, it?.descKey, '');
export const npcName = (lang: Lang, n: any) => g(lang, n?.nameKey, n?.id ?? '?');
export const monsterName = (lang: Lang, m: any) => g(lang, m?.nameKey, m?.id ?? '?');

const spoilerSet = new Set<string>(spoilersJson.list);
export const isSpoiler = (kind: string, id: string) => spoilerSet.has(`${kind}:${id}`);

export const petUrl = (lang: Lang, id: string) => `/${lang.slug}/pets/${id}/`;
export const base = (lang: Lang) => `/${lang.slug}/`;
export const itemUrl = (lang: Lang, id: string) => `${base(lang)}items/${slug(id)}/`;
export const npcUrl = (lang: Lang, id: string) => `${base(lang)}characters/${slug(id)}/`;
export const monsterUrl = (lang: Lang, id: string) => `${base(lang)}monsters/${slug(id)}/`;
export const plantUrl = (lang: Lang, id: string) => `${base(lang)}plants/${slug(id)}/`;
export const slug = (id: string) => id.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

export const ITEM_TYPES = ['Weapon', 'Food', 'Placeable', 'Ingredients', 'Guidebook', 'Treasure', 'Flower', 'Plant', 'LoreBook', 'Fish'];
export const STATIONS = ['Workbench', 'Stove', 'Furnance', 'Forge', 'Anvil', 'AlchemyTable', 'WineBarrel', 'OilMaker', 'JamMaker', 'Composter', 'TailoringTable', 'PlayerHands'];
export const TICK_SECONDS = 0.25;
export const allLangs = LANGS;

export function staticLangPaths() {
  return LANGS.map((l) => ({ params: { lang: l.slug }, props: { lang: l } }));
}

const SCENE_AREA: Record<string, string> = {
  World: 'Bloomrise_AreaData 1', Bar: 'Bar_AreaData', Biblioteca: 'Biblioteca_AreaData 3', Ferreiro: 'Ferreiro_AreaData 2', RayyHouse: 'RayyHouse_AreaData',
  JadenHouse: 'Jaden_AreaData', LupiHouse: 'LupiHouse_AreaData 1', LylaHouse: 'Lyla_AreaData', MiloHouse: 'Milo_AreaData', SeleneHouse: 'Selene_AreaData',
  VictorHouse: 'Victor_AreaData 1', WadeHouse: 'Wade_AreaData 1', MabelHouse: 'Mabel_AreaData', Arcania: 'Arcania_AreaData',
};
const areaKey = new Map((areasJson as any[]).map((a) => [a.id, a.nameKey]));
/** Nome localizado da area de uma cena (cai no nome interno se nao houver). */
export const sceneLabel = (lang: Lang, scene: string) => g(lang, areaKey.get(SCENE_AREA[scene] ?? ''), scene);

/** Navegacao: grupos do menu (cada categoria vira uma pagina /<lang>/<slug>/). */
export const NAV_GROUPS = [
  { key: 'gWorld', cats: ['map', 'characters', 'pets', 'shops', 'monsters'] },
  { key: 'gItems', cats: ['items', 'crafting', 'plants', 'fishing'] },
  { key: 'gProgress', cats: ['quests', 'skills', 'guide'] },
];
export const ALL_CATS = [...NAV_GROUPS.flatMap((g) => g.cats), 'mechanics'];

const CAT_ICON_ITEM: Record<string, string> = {
  items: 'ITEM_CHEST', crafting: 'Ferro', shops: 'Ouro', fishing: 'RainbowTrout', quests: 'CronicasDeRook', guide: 'guide', mechanics: 'CPU', map: 'AmuletoCasa',
};
/** Sprite (arquivo em /sprites/) que representa uma categoria. */
export function catIcon(cat: string): string | null {
  if (CAT_ICON_ITEM[cat]) return itemById.get(CAT_ICON_ITEM[cat])?.icon ?? null;
  if (cat === 'characters') return npcById.get('Darius')?.icon ?? null;
  if (cat === 'pets') return pets.find((p) => p.id === 'dog')?.icon ?? null;
  if (cat === 'monsters') return monsterById.get('zombie')?.icon ?? null;
  if (cat === 'plants') return plantById.get('DadosCenoura')?.stages?.slice(-1)[0] ?? null;
  if (cat === 'skills') return skillById.get('LastResort')?.icon ?? skills[0]?.icon ?? null;
  return null;
}
export const FEATURED_ITEMS = ['Iron Axe', 'Bow', 'Hamburger', 'sushi', 'potion_legendary', 'bomb', 'AmuletoCasa', 'RainbowTrout', 'Seed_morango', 'DetectorMetal', 'Pizza', 'GoldSword'];
export const LINKS = {
  steam: 'https://store.steampowered.com/app/4383630/Tales_of_Bloomrise/',
  play: 'https://play.google.com/store/apps/details?id=com.minelli.talesofbloomrise',
  discord: 'https://discord.gg/4QSxuG7RK7',
  site: 'https://talesofbloomrise.com',
};
