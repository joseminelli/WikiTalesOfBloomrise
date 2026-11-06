# Wiki de Tales Of Bloomrise

Código-fonte da wiki publicada em **https://wiki.talesofbloomrise.com**: site estático ([Astro](https://astro.build) + [Pagefind](https://pagefind.app)), 9 idiomas, busca, modo spoiler, sprites animados de NPCs, monstros e pets.

## Como funciona

- Os **dados do jogo** (itens, receitas, NPCs, monstros, pets...) e os **sprites** são extraídos automaticamente dos `Assets` do projeto Unity por um script do projeto do jogo e ficam versionados aqui em `src/data/` e `public/sprites/`.
- Os textos vêm da localização do próprio jogo (`src/data/i18n/*.json`, 9 idiomas); a interface do site está em `src/lib/i18n.ts` e `src/lib/i18n-pets.ts`.
- As páginas de **mecânicas** são Markdown em `src/content/mechanics/<tema>.<idioma>.md`.
- Marcações de spoiler: `src/data/spoilers.json`.

## Rodar localmente

```bash
npm install
npm run dev        # http://localhost:4321
```

## Publicar

O GitHub Pages serve o branch `gh-pages` (domínio no arquivo `public/CNAME`).

```bash
npm install
npm run deploy     # gera o site e publica a pasta dist/ no branch gh-pages
```

(`npm run build` só gera `dist/`.) O arquivo `public/.nojekyll` é necessário para o GitHub não ignorar a pasta `_astro`.

## Atualizar o conteúdo depois de mudar o jogo

No projeto do jogo, rodar o exportador (`npm run all` na pasta `Wiki` de lá) e copiar `src/` e `public/` atualizados para este repositório; depois `npm run deploy`.

---
O repositório anterior (MkDocs) está preservado no branch `legacy-mkdocs`.
