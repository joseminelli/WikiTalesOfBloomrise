# 🌸 Tales of Bloomrise - Wiki System

Este repositório contém o sistema automatizado de geração da Wiki oficial de **Tales of Bloomrise**. A documentação é gerada dinamicamente a partir dos arquivos de dados do jogo (`JSON/CSV`) e publicada via GitHub Pages.

## 🛠️ Tecnologias Utilizadas
- **Python**: Processamento de dados e geração de Markdown.
- **MkDocs / Material Theme**: Renderização do site estático.
- **GitHub Pages**: Hospedagem gratuita da Wiki.

## 📁 Estrutura de Pastas
- `docs/`: Contém os arquivos manuais (`index.md`, personagens, etc).
- `assets/`: Imagens de itens, ícones e sprites.
- `scripts/`: Scripts Python que transformam dados em páginas da Wiki.
- `data/`: Arquivos de dados (JSON/CSV) extraídos do jogo.

## 🚀 Como Atualizar e Publicar

Como as GitHub Actions estão desativadas, o processo de publicação é feito manualmente através do seu terminal. Siga estes passos sempre que fizer alterações:

### 1. Gerar novos conteúdos
Rode o script para converter os dados do jogo em páginas Markdown:
```bash
python scripts/build_wiki.py

```

### 2. Publicar na Web

Use o comando do MkDocs para compilar o site e enviar para o subdomínio `wiki.talesofbloomrise.com`:

```bash

.venv\Scripts\activate

```

```bash

mkdocs gh-deploy --force

```

### 3. Salvar o código fonte

Não esqueça de comitar as alterações do seu código e dos arquivos de dados:

```bash
git add .
git commit -m "Update: novas receitas e ajustes visuais nos itens"
git push origin main

```

## ⚠️ Observações Importantes

* **Imagens**: O servidor diferencia maiúsculas de minúsculas. Certifique-se de que os nomes dos arquivos na pasta `img/` (ex: `Rayy.webp`) coincidem exatamente com as referências nos textos.
* **Pasta /site**: Esta pasta é gerada localmente e **não deve ser enviada para o Git** (já está no `.gitignore`).
* **Domínio**: A configuração de DNS está vinculada ao arquivo `CNAME` gerado automaticamente pelo `mkdocs.yml`.

---

*Wiki desenvolvida para o universo de Tales of Bloomrise.*
