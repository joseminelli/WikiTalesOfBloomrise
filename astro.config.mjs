import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://wiki.talesofbloomrise.com',
  output: 'static',
  trailingSlash: 'always',
  build: { format: 'directory' },
  devToolbar: { enabled: false },
});
