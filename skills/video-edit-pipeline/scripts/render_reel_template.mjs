#!/usr/bin/env node
/** Render a local, source-backed vertical reel. Run --help; never edits Borumi. */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const template = path.resolve(here, '../assets/reel-template');
const imageExtensions = new Set(['.png', '.jpg', '.jpeg', '.webp', '.svg']);
const videoExtensions = new Set(['.mp4', '.mov', '.m4v', '.webm']);
const fail = message => { throw new Error(message); };
const object = (x, where) => (!x || typeof x !== 'object' || Array.isArray(x)) ? fail(`${where}: expected an object`) : x;
const keys = (x, allowed, where) => Object.keys(object(x, where)).forEach(k => { if (!allowed.includes(k)) fail(`${where}: unknown field ${k}`); });
const number = (x, where, min = 0, max = Infinity) => (!Number.isFinite(x) || x < min || x > max) ? fail(`${where}: invalid number`) : x;
const text = (x, where, max, empty = false) => (typeof x !== 'string' || (!empty && !x.trim()) || x.length > max) ? fail(`${where}: invalid text`) : x;
const expand = p => p.startsWith('~/') ? path.join(os.homedir(), p.slice(2)) : p;
const sha = value => crypto.createHash('sha256').update(value).digest('hex');

export function validatePlan(raw, baseDir, {probeMedia = true} = {}) {
  keys(raw, ['version', 'fps', 'scenes'], 'plan');
  if (raw.version !== 1) fail('plan.version must be 1');
  const fps = raw.fps ?? 30;
  if (![30, 60].includes(fps)) fail('fps must be 30 or 60');
  if (!Array.isArray(raw.scenes) || !raw.scenes.length || raw.scenes.length > 24) fail('Use 1–24 scenes');
  const assets = new Map();
  const probes = new Map();
  const ids = new Set();
  let cursor = 0;
  function source(s, where, kind, frames) {
    text(s.path, `${where}.path`, 4096);
    if (/^[a-z][a-z0-9+.-]*:\/\//i.test(s.path) || /^(data|file):/i.test(s.path)) fail(`${where}: use a local file path`);
    const file = fs.realpathSync(path.resolve(baseDir, expand(s.path)));
    const stat = fs.statSync(file);
    if (!stat.isFile()) fail(`${where}: not a regular file`);
    const ext = path.extname(file).toLowerCase();
    if (!(kind === 'image' ? imageExtensions : videoExtensions).has(ext)) fail(`${where}: unsupported ${kind} extension`);
    if (!assets.has(file)) assets.set(file, {path: file, publicName: `asset-${assets.size}${ext}`, bytes: stat.size, mtimeMs: stat.mtimeMs});
    let position = s.position ?? [0.5, 0.5];
    if (!Array.isArray(position) || position.length !== 2) fail(`${where}.position requires [x,y]`);
    position = position.map((v, i) => number(v, `${where}.position[${i}]`, 0, 1));
    const result = {src: assets.get(file).publicName, position};
    if (kind === 'video') {
      number(s.source_start_s, `${where}.source_start_s`);
      number(s.source_end_s, `${where}.source_end_s`);
      result.startFrame = Math.round(s.source_start_s * fps);
      result.endFrame = Math.round(s.source_end_s * fps);
      if (result.endFrame - result.startFrame < frames) fail(`${where}: source range is shorter than the scene`);
      if (probeMedia) {
        if (!probes.has(file)) {
          const p = JSON.parse(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration:stream=codec_type', '-of', 'json', file], {encoding: 'utf8'}));
          if (!p.streams?.some(s => s.codec_type === 'video') || !Number.isFinite(Number(p.format?.duration))) fail(`${where}: video duration unavailable`);
          probes.set(file, Number(p.format.duration));
        }
        if (s.source_end_s > probes.get(file) + 1 / fps) fail(`${where}: source range exceeds the media duration`);
      }
    } else if (s.source_start_s !== undefined || s.source_end_s !== undefined) fail(`${where}: image sources have no video range`);
    return result;
  }
  const scenes = raw.scenes.map((s, index) => {
    const where = `scenes[${index}]`;
    keys(s, ['id', 'duration_s', 'heading', 'camera', 'proof', 'captions', 'cta'], where);
    text(s.id, `${where}.id`, 64);
    if (!/^[a-zA-Z0-9_-]+$/.test(s.id) || ids.has(s.id)) fail(`${where}: scene IDs must be unique and use letters, digits, _ or -`);
    ids.add(s.id);
    number(s.duration_s, `${where}.duration_s`, 1 / fps, 120);
    const frames = Math.round(s.duration_s * fps);
    const out = {id: s.id, fromFrame: cursor, durationInFrames: frames, heading: '', captions: []};
    cursor += frames;
    if (s.heading !== undefined) out.heading = text(s.heading, `${where}.heading`, 64, true);
    if (s.camera !== undefined) {
      keys(s.camera, ['path', 'source_start_s', 'source_end_s', 'position', 'muted'], `${where}.camera`);
      if (s.camera.muted !== undefined && typeof s.camera.muted !== 'boolean') fail(`${where}.camera.muted must be boolean`);
      out.camera = {...source(s.camera, `${where}.camera`, 'video', frames), muted: s.camera.muted ?? false};
    }
    if (s.proof !== undefined) {
      keys(s.proof, ['path', 'kind', 'label', 'verified', 'source_url', 'captured_at', 'source_start_s', 'source_end_s', 'position'], `${where}.proof`);
      if (!['image', 'video'].includes(s.proof.kind) || s.proof.verified !== true) fail(`${where}.proof requires kind image/video and verified:true`);
      text(s.proof.label, `${where}.proof.label`, 72);
      for (const k of ['source_url', 'captured_at']) if (s.proof[k] !== undefined) text(s.proof[k], `${where}.proof.${k}`, 2048);
      out.proof = {...source(s.proof, `${where}.proof`, s.proof.kind, frames), kind: s.proof.kind, label: s.proof.label, muted: true};
    }
    if (s.captions !== undefined && (!Array.isArray(s.captions) || s.captions.length > 300)) fail(`${where}.captions: expected an array of at most 300`);
    let priorEnd = 0;
    out.captions = (s.captions ?? []).map((c, n) => {
      const at = `${where}.captions[${n}]`;
      keys(c, ['start_s', 'end_s', 'text', 'highlight'], at);
      number(c.start_s, `${at}.start_s`, 0, frames / fps);
      number(c.end_s, `${at}.end_s`, 0, frames / fps);
      const startFrame = Math.round(c.start_s * fps), endFrame = Math.round(c.end_s * fps);
      if (startFrame < priorEnd || endFrame <= startFrame) fail(`${at}: captions must be ordered, nonoverlapping, and nonempty`);
      priorEnd = endFrame;
      text(c.text, `${at}.text`, 80);
      if (c.text.trim().split(/\s+/).length > 7) fail(`${at}: use at most 7 words per caption`);
      if (c.highlight !== undefined && (!Array.isArray(c.highlight) || c.highlight.length > 7)) fail(`${at}.highlight: expected up to 7 words`);
      const highlight = (c.highlight ?? []).map(w => text(w, `${at}.highlight`, 80).replace(/[^\p{L}\p{N}]/gu, '').toLowerCase());
      return {startFrame, endFrame, text: c.text.trim(), highlight};
    });
    if (s.cta !== undefined) {
      keys(s.cta, ['text', 'eyebrow', 'subtitle'], `${where}.cta`);
      if (index !== raw.scenes.length - 1) fail('CTA belongs in the final scene');
      if (out.captions.length) fail('Use CTA or captions in the final scene, not both');
      out.cta = {text: text(s.cta.text, `${where}.cta.text`, 24)};
      for (const [k, max] of [['eyebrow', 32], ['subtitle', 72]]) if (s.cta[k] !== undefined) out.cta[k] = text(s.cta[k], `${where}.cta.${k}`, max, true);
    }
    return out;
  });
  if (cursor > 180 * fps) fail('This reel template is limited to 180 seconds');
  return {plan: {fps, durationInFrames: cursor, scenes}, assets: [...assets.values()]};
}

function options(argv) {
  const out = {};
  const switches = new Set(['help', 'check', 'still-only', 'overwrite', 'keep-work']);
  const values = new Set(['plan', 'output', 'deps', 'quality', 'still', 'at', 'concurrency', 'browser']);
  for (let i = 0; i < argv.length; i++) {
    const key = argv[i].replace(/^--/, '');
    if (!argv[i].startsWith('--') || (!switches.has(key) && !values.has(key))) fail(`Unknown option ${argv[i]}`);
    if (switches.has(key)) out[key] = true;
    else { if (!argv[i + 1] || argv[i + 1].startsWith('--')) fail(`Missing value for --${key}`); out[key] = argv[++i]; }
  }
  return out;
}

const help = `Render a styled 9:16 reel from local assets (no Borumi writes or provider calls).
  node render_reel_template.mjs --plan plan.json --output reel.mp4 [options]
  --quality preview|final  540x960 or 1080x1920, default preview
  --deps DIR              Directory with installed Remotion node_modules
  --still frame.png --at 1 Also save a frame at reel time 1 second
  --still-only            Render only --still; --output is unnecessary
  --check                 Validate ranges/files and print a compact plan, no renderer
  --concurrency N         Local render workers (1–8, default 2)
  --browser PATH          Existing headless browser; otherwise discover cached Chrome
  --overwrite             Replace the named output(s)
  --keep-work             Retain isolated temporary render files for debugging
See assets/reel-template/README.md and schema.json. Receipts contain private paths.`;

async function fileHash(file) {
  const hash = crypto.createHash('sha256');
  for await (const chunk of fs.createReadStream(file)) hash.update(chunk);
  return hash.digest('hex');
}

function dependencies(arg) {
  const candidates = (arg ? [arg] : [process.env.REMOTION_DEPS, template, path.join(process.env.BORUMI_AGENT_HOME || path.join(os.homedir(), '.borumi-agent'), 'animation-kit')]).filter(Boolean);
  const dir = candidates.map(p => path.resolve(expand(p))).find(p => fs.existsSync(path.join(p, 'node_modules/remotion/package.json')));
  if (!dir) fail('Remotion dependencies missing. Install assets/reel-template/package.json or pass --deps DIR. No automatic install was attempted.');
  const require = createRequire(path.join(dir, 'package.json'));
  const versions = Object.fromEntries(['remotion', '@remotion/bundler', '@remotion/renderer', 'react'].map(p => [p, require(`${p}/package.json`).version]));
  if (new Set(['remotion', '@remotion/bundler', '@remotion/renderer'].map(p => versions[p])).size !== 1) fail('All Remotion packages must have the same version');
  return {dir, require, versions};
}

function browser(deps, explicit) {
  if (explicit) return fs.realpathSync(path.resolve(expand(explicit)));
  const cache = path.join(deps, 'node_modules/.remotion/chrome-headless-shell');
  if (fs.existsSync(cache)) {
    for (const platform of fs.readdirSync(cache)) {
      const base = path.join(cache, platform);
      if (!fs.statSync(base).isDirectory()) continue;
      for (const sub of fs.readdirSync(base)) for (const name of ['chrome-headless-shell', 'chrome-headless-shell.exe']) {
        const candidate = path.join(base, sub, name);
        if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) return candidate;
      }
    }
  }
  fail('No cached headless browser found. Pass --browser PATH or run Remotion browser setup once. No browser download was attempted.');
}

export async function main(argv = process.argv.slice(2)) {
  const opt = options(argv);
  if (opt.help) { console.log(help); return; }
  if (!opt.plan) fail('--plan is required');
  const planFile = fs.realpathSync(path.resolve(expand(opt.plan)));
  const rawText = fs.readFileSync(planFile, 'utf8');
  const {plan, assets} = validatePlan(JSON.parse(rawText), path.dirname(planFile));
  const summary = {duration_s: plan.durationInFrames / plan.fps, fps: plan.fps, scenes: plan.scenes.length, assets: assets.length};
  if (opt.check) { console.log(JSON.stringify({valid: true, ...summary}, null, 2)); return; }
  if (opt['still-only'] ? !opt.still : !opt.output) fail(opt['still-only'] ? '--still-only requires --still' : '--output is required');
  const quality = opt.quality ?? 'preview';
  if (!['preview', 'final'].includes(quality)) fail('--quality must be preview or final');
  const concurrency = Number(opt.concurrency ?? 2);
  if (!Number.isInteger(concurrency) || concurrency < 1 || concurrency > 8) fail('--concurrency must be 1–8');
  const at = Number(opt.at ?? Math.min(1, (plan.durationInFrames - 1) / plan.fps));
  number(at, '--at', 0, (plan.durationInFrames - 1) / plan.fps);
  const outputs = [];
  for (const [key, ext] of [['output', '.mp4'], ['still', '.png']]) if (opt[key] && !(key === 'output' && opt['still-only'])) {
    const target = path.resolve(expand(opt[key]));
    if (path.extname(target).toLowerCase() !== ext) fail(`--${key} must end with ${ext}`);
    const existing = fs.existsSync(target) ? fs.realpathSync(target) : target;
    if (existing === planFile || assets.some(a => a.path === existing)) fail('Output must not replace an input');
    if (!opt.overwrite && (fs.existsSync(target) || fs.existsSync(`${target}.receipt.json`))) fail(`Output already exists: ${target}. Choose another path or use --overwrite.`);
    fs.mkdirSync(path.dirname(target), {recursive: true});
    outputs.push({key, target});
  }
  const dep = dependencies(opt.deps);
  const browserExecutable = browser(dep.dir, opt.browser);
  const {bundle} = dep.require('@remotion/bundler');
  const {selectComposition, renderMedia, renderStill} = dep.require('@remotion/renderer');
  const work = fs.mkdtempSync(path.join(os.tmpdir(), 'video-edit-pipeline-reel-'));
  const scale = quality === 'preview' ? 0.5 : 1;
  const started = Date.now();
  try {
    fs.mkdirSync(path.join(work, 'public'));
    fs.copyFileSync(path.join(template, 'index.jsx'), path.join(work, 'index.jsx'));
    fs.copyFileSync(path.join(template, 'package.json'), path.join(work, 'package.json'));
    fs.symlinkSync(path.join(dep.dir, 'node_modules'), path.join(work, 'node_modules'), 'junction');
    for (const a of assets) {
      a.sha256 = await fileHash(a.path);
    }
    const templateSha = sha(fs.readFileSync(path.join(template, 'index.jsx')));
    const inputProps = {plan};
    console.error(`Rendering ${summary.duration_s.toFixed(2)}s at ${1080 * scale}x${1920 * scale}; ${assets.length} local assets`);
    const serveUrl = await bundle({entryPoint: path.join(work, 'index.jsx'), outDir: path.join(work, 'bundle'), rootDir: work,
      publicDir: path.join(work, 'public'), symlinkPublicDir: false, enableCaching: false,
      onSymlinkDetected: () => {}, onProgress: () => {}});
    // Renderer static serving can reject symlinks outside its root. Clone/copy each
    // selected asset once into the finished bundle, never the entire source folder.
    fs.mkdirSync(path.join(serveUrl, 'public'), {recursive: true});
    for (const a of assets) fs.copyFileSync(a.path, path.join(serveUrl, 'public', a.publicName), fs.constants.COPYFILE_FICLONE);
    const composition = await selectComposition({serveUrl, id: 'VerticalProofReel', inputProps, browserExecutable, logLevel: 'error'});
    for (const out of outputs) {
      out.temp = path.join(work, out.key === 'still' ? 'frame.png' : 'reel.mp4');
      if (out.key === 'still') await renderStill({serveUrl, composition, inputProps, browserExecutable, scale,
        frame: Math.round(at * plan.fps), output: out.temp, imageFormat: 'png', logLevel: 'error'});
      else await renderMedia({serveUrl, composition, inputProps, browserExecutable, scale, concurrency,
        codec: 'h264', crf: quality === 'preview' ? 25 : 18, pixelFormat: 'yuv420p', audioCodec: 'aac',
        enforceAudioTrack: true, outputLocation: out.temp, logLevel: 'error', overwrite: false});
    }
    for (const a of assets) { const s = fs.statSync(a.path); if (s.size !== a.bytes || s.mtimeMs !== a.mtimeMs) fail(`Source changed during render: ${a.path}`); }
    const receipt = {version: 1, generated_at: new Date().toISOString(), plan_sha256: sha(rawText), template_sha256: templateSha,
      renderer_versions: dep.versions, quality, width: 1080 * scale, height: 1920 * scale, ...summary,
      sources: assets, scene_ranges: plan.scenes.map(s => ({id: s.id, start_frame: s.fromFrame, end_frame: s.fromFrame + s.durationInFrames})),
      elapsed_s: Math.round((Date.now() - started) / 100) / 10};
    for (const out of outputs) {
      fs.copyFileSync(out.temp, out.target, opt.overwrite ? 0 : fs.constants.COPYFILE_EXCL);
      const output_sha256 = await fileHash(out.target);
      fs.writeFileSync(`${out.target}.receipt.json`, JSON.stringify({...receipt, output: out.target, output_sha256,
        ...(out.key === 'still' ? {still_frame: Math.round(at * plan.fps)} : {})}, null, 2) + '\n', {flag: opt.overwrite ? 'w' : 'wx'});
      console.log(JSON.stringify({output: out.target, sha256: output_sha256, receipt: `${out.target}.receipt.json`}));
    }
  } finally {
    if (opt['keep-work']) console.error(`Work retained: ${work}`);
    else fs.rmSync(work, {recursive: true, force: true});
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(error => { console.error(`reel-template: ${error.message}`); process.exitCode = 1; });
}
