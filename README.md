# Wiki de Tales Of Bloomrise

Código-fonte da wiki publicada em **https://wiki.talesofbloomrise.com** (site estático com [Astro](https://astro.build) e [Pagefind](https://pagefind.app); 9 idiomas, busca, modo spoiler, sprites animados).

> Este repositório é **gerado automaticamente** a partir do projeto do jogo (comando `npm run deploy:github` na pasta `Wiki` de lá). Os dados do jogo (`src/data/`) e os sprites (`public/sprites/`) são extraídos dos `Assets` do Unity; edições feitas direto aqui serão sobrescritas na próxima publicação.

- `gh-pages`: site gerado, servido pelo GitHub Pages (domínio em `public/CNAME`).
- `legacy-mkdocs`: a wiki antiga (MkDocs).

## Rodar localmente

```bash
npm install
npm run dev      # http://localhost:4321
npm run build    # gera dist/
```
