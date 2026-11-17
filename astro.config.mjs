import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  // Where the site lives. Canonical links, the sitemap and share images are built from it.
  // Set SITE_URL to build for another address, such as a staging one.
  site: process.env.SITE_URL || 'https://www.pucksley.com',
  integrations: [
    tailwind(),
    sitemap({
      filter: (page) => !/\/video\/?$/.test(page),
    }),
  ],
  output: 'static',
  // /video is the obvious guess; the film lives at /videos.
  redirects: { '/video': '/videos/' },
  // The sibling sites use 4331 to 4335 (dimpkin.com 4332, spacetofeel.com 4334, trialheat.com 4335):
  // shifted by one more so all of them can run locally at the same time.
  server: { port: 4336 },
  // film/ holds the film's source and several gigabytes of rendered pictures. The dev server has no
  // reason to watch it.
  vite: { server: { watch: { ignored: ['**/film/**', '**/design/**'] } } },
});
