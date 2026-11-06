import type { Lang } from './i18n';

// Arquivos: src/content/mechanics/<slug>.<idioma>.md  (idioma = slug do idioma: pt-br, en, es...)
// Frontmatter: title, icon, order, summary, related: [categorias do wiki]
const files = import.meta.glob('../content/mechanics/*.md', { eager: true }) as Record<string, any>;

interface Entry { slug: string; langSlug: string; frontmatter: any; Content: any; headings: { depth: number; slug: string; text: string }[]; minutes: number }
const entries: Entry[] = Object.entries(files).map(([path, mod]) => {
  const file = path.split('/').pop()!.replace(/\.md$/, '');
  const i = file.indexOf('.');
  const raw: string = typeof mod.rawContent === 'function' ? mod.rawContent() : '';
  // CJK conta por caractere; demais idiomas por palavra (~200 palavras/min, ~400 caracteres/min)
  const cjk = (raw.match(/[㐀-鿿]/g) || []).length;
  const words = raw.split(/\s+/).filter(Boolean).length;
  const minutes = Math.max(1, Math.round(cjk > 50 ? cjk / 400 : words / 200));
  return { slug: file.slice(0, i), langSlug: file.slice(i + 1), frontmatter: mod.frontmatter ?? {}, Content: mod.Content, headings: (mod.getHeadings?.() ?? []).filter((h: any) => h.depth === 2), minutes };
});

export const mechanicSlugs = () => [...new Set(entries.map((e) => e.slug))];

export function resolveMechanic(lang: Lang, slug: string) {
  const own = entries.find((e) => e.slug === slug && e.langSlug === lang.slug);
  if (own) return { entry: own, fallback: false };
  const en = entries.find((e) => e.slug === slug && e.langSlug === 'en')!;
  return { entry: en, fallback: true };
}

export function mechanicsFor(lang: Lang) {
  return mechanicSlugs()
    .map((slug) => {
      const { entry, fallback } = resolveMechanic(lang, slug);
      const fm = entry.frontmatter;
      return {
        slug, fallback, title: fm.title as string, icon: (fm.icon as string) ?? '', order: (fm.order as number) ?? 99,
        summary: (fm.summary as string) ?? '', related: (fm.related as string[]) ?? [], minutes: entry.minutes, headings: entry.headings,
      };
    })
    .sort((a, b) => a.order - b.order);
}
