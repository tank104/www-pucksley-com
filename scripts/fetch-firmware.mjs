// Before every build: the puck's firmware from Pucksley's latest release, for the flasher on /flash/.
// The browser flasher can only read files from this site (GitHub's downloads don't allow other sites
// to read them), so the release's pucksley-firmware.zip is unpacked into public/firmware/ with a
// manifest for ESP Web Tools. No release yet, or no network: the page says so and the build goes on.
//
//   node scripts/fetch-firmware.mjs       (npm run build runs it first)
//   PUCKSLEY_FIRMWARE=<zip> …             a zip of your own instead (a local build, to try the page)
import { execFileSync } from 'node:child_process';
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync, cpSync, mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const RELEASE = 'https://github.com/tank104/Pucksley/releases/latest/download/pucksley-firmware.zip';
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const target = join(root, 'public', 'firmware');

const work = mkdtempSync(join(tmpdir(), 'pucksley-firmware-'));
try {
  const zip = join(work, 'firmware.zip');
  if (process.env.PUCKSLEY_FIRMWARE) {
    cpSync(process.env.PUCKSLEY_FIRMWARE, zip);
  } else {
    const response = await fetch(RELEASE, { redirect: 'follow' });
    if (!response.ok) throw new Error(`the latest release has no firmware (${response.status})`);
    writeFileSync(zip, Buffer.from(await response.arrayBuffer()));
  }

  // unzip where there is one (Linux, macOS); Windows' own tar reads zips
  try {
    execFileSync('unzip', ['-q', zip, '-d', work], { stdio: 'ignore' });
  } catch {
    execFileSync('tar', ['-xf', zip, '-C', work], { stdio: 'ignore' });
  }
  const unpacked = join(work, 'pucksley-firmware');
  const version = readFileSync(join(unpacked, 'version.txt'), 'utf8').trim();

  // flash_args: option lines, then "<offset> <file>" for each image, in the order idf.py flashes them
  const parts = readFileSync(join(unpacked, 'flash_args'), 'utf8')
    .split('\n')
    .map((line) => line.trim().match(/^(0x[0-9a-f]+)\s+(\S+)$/i))
    .filter(Boolean)
    .map(([, offset, path]) => {
      if (!existsSync(join(unpacked, path))) throw new Error(`flash_args names ${path}, which isn't in the zip`);
      return { path, offset: Number.parseInt(offset, 16) };
    });
  if (!parts.some((p) => p.offset === 0x10000)) throw new Error("flash_args has no app at 0x10000");

  rmSync(target, { recursive: true, force: true });
  mkdirSync(target, { recursive: true });
  cpSync(unpacked, target, { recursive: true });
  writeFileSync(
    join(target, 'manifest.json'),
    JSON.stringify(
      {
        name: 'Pucksley',
        version,
        // A puck that has never had Pucksley is offered a clean slate; an update keeps its Wi-Fi and
        // its pairing with the hub (they live in a part of the flash none of these images touch)
        new_install_prompt_erase: true,
        builds: [{ chipFamily: 'ESP32-S3', parts }],
      },
      null,
      2,
    ),
  );
  console.log(`firmware ${version}: ${parts.map((p) => `0x${p.offset.toString(16)} ${p.path}`).join(', ')}`);
} catch (e) {
  console.warn(`No firmware for /flash/ (${e.message}): the page will say there's no release yet.`);
} finally {
  rmSync(work, { recursive: true, force: true });
}
