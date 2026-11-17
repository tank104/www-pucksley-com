// Build-time content reader.
//
// Content lives as plain JSON files in the repo, read at build time with Vite's
// `import.meta.glob`. This mirrors the sibling sites' reader pattern
// (`singletons.<name>.read()` / `collections.<name>.all()`), so the site is ready to be wired up
// to a git-based CMS (e.g. Sveltia) later without touching how pages and components fetch content:
// only the editing surface changes, not the on-disk file shapes.

import type { Light } from './site';
import type { Line } from './films';

type Json = Record<string, any>;

const PAGE_FILES = import.meta.glob<Json>('../content/pages/*.json', { eager: true, import: 'default' });
const SETTING_FILES = import.meta.glob<Json>('../content/settings/*.json', { eager: true, import: 'default' });
const MOMENT_FILES = import.meta.glob<Json>('../content/moments/*.json', { eager: true, import: 'default' });
const PLUGIN_FILES = import.meta.glob<Json>('../content/plugins/*.json', { eager: true, import: 'default' });
const FAQ_FILES = import.meta.glob<Json>('../content/faq/*.json', { eager: true, import: 'default' });

function bySlug(modules: Record<string, Json>, basename: string): Json | null {
  const hit = Object.entries(modules).find(([path]) => path.endsWith(`/${basename}.json`));
  return hit ? hit[1] : null;
}

function asEntries(modules: Record<string, Json>): { slug: string; entry: Json }[] {
  return Object.entries(modules).map(([path, entry]) => ({
    slug: path.split('/').pop()!.replace(/\.json$/, ''),
    entry,
  }));
}

const SINGLETONS: Record<string, () => Json | null> = {
  home: () => bySlug(PAGE_FILES, 'home'),
  siteSettings: () => bySlug(SETTING_FILES, 'site'),
};

const COLLECTIONS: Record<string, Record<string, Json>> = {
  moments: MOMENT_FILES,
  plugins: PLUGIN_FILES,
  faq: FAQ_FILES,
};

type SingletonReader = { read: () => Promise<Json | null> };
type CollectionReader = { all: () => Promise<{ slug: string; entry: Json }[]> };

export const reader = {
  singletons: Object.fromEntries(
    Object.entries(SINGLETONS).map(([name, get]) => [name, { read: async () => get() }]),
  ) as Record<string, SingletonReader>,
  collections: Object.fromEntries(
    Object.entries(COLLECTIONS).map(([name, mods]) => [name, { all: async () => asEntries(mods) }]),
  ) as Record<string, CollectionReader>,
};

async function ordered<T extends { order: number }>(name: string): Promise<T[]> {
  const entries = await reader.collections[name].all();
  return entries.map((e) => ({ slug: e.slug, ...e.entry }) as unknown as T).sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
}

/** One of the puck's faces (public/images/faces/<name>.webp, made by film/web.py from the simulator's pictures). */
export type FaceRef = { name: string; alt: string };

// One file per moment of the film's day, read by Day.astro, in the film's order.
export type Moment = {
  slug: string;
  order: number;
  /** The part of the day, as the page labels it ("First light"), and the light it is shown in. */
  when: string;
  light: Light;
  /** Where this moment starts in the film, in seconds. */
  at: number;
  heading: string;
  said: Line[];
  body: string;
  /** What the house did, in the film. */
  house: string;
  faces: FaceRef[];
  /** A still from the film (public/images/film/<name>-<1280|640>.jpg). */
  still: { name: string; alt: string };
};
export const getMoments = () => ordered<Moment>('moments');

// What the hub's plugins run, one file each.
export type Plugin = { slug: string; order: number; title: string; where: string; body: string };
export const getPlugins = () => ordered<Plugin>('plugins');

export type FaqItemT = { slug: string; order: number; question: string; answer: string; openByDefault: boolean };
export const getFaqItems = () => ordered<FaqItemT>('faq');
