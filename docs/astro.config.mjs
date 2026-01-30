import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

// For GitHub Pages: set base to '/nokwatch/' when building for jimididit.github.io/nokwatch
export default defineConfig({
  integrations: [tailwind()],
  site: 'https://jimididit.github.io',
  base: '/nokwatch',
  trailingSlash: 'always',
});
