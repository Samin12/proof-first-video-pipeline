import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validatePlan} from '../skills/video-edit-pipeline/scripts/render_reel_template.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const template = path.join(root, 'skills/video-edit-pipeline/assets/reel-template');
const fixture = () => JSON.parse(fs.readFileSync(path.join(template, 'example.json'), 'utf8'));

test('synthetic plan has exact consecutive frame boundaries and a source asset', () => {
  const {plan, assets} = validatePlan(fixture(), template);
  assert.equal(plan.durationInFrames, 120);
  assert.deepEqual(plan.scenes.map(s => [s.fromFrame, s.durationInFrames]), [[0, 60], [60, 60]]);
  assert.equal(assets.length, 1);
});

test('unverified and remote proof sources are rejected before render', () => {
  const a = fixture(); a.scenes[0].proof.verified = false;
  assert.throws(() => validatePlan(a, template), /verified:true/);
  const b = fixture(); b.scenes[0].proof.path = 'https://example.com/image.png';
  assert.throws(() => validatePlan(b, template), /local file/);
});

test('caption overlaps and text too long for the template are rejected', () => {
  const a = fixture(); a.scenes[0].captions.push({start_s: 1, end_s: 2, text: 'OVERLAP'});
  assert.throws(() => validatePlan(a, template), /nonoverlapping/);
  const b = fixture(); b.scenes[0].captions[0].text = 'ONE TWO THREE FOUR FIVE SIX SEVEN EIGHT';
  assert.throws(() => validatePlan(b, template), /7 words/);
});

test('source ranges use composition frame time and cannot be shorter than the scene', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'reel-schema-test-'));
  try {
    fs.writeFileSync(path.join(dir, 'camera.mov'), 'not decoded in this structural test');
    const raw = {version: 1, fps: 30, scenes: [{id: 'one', duration_s: 2, camera: {path: 'camera.mov', source_start_s: 10, source_end_s: 12}}]};
    const {plan} = validatePlan(raw, dir, {probeMedia: false});
    assert.equal(plan.scenes[0].camera.startFrame, 300);
    assert.equal(plan.scenes[0].camera.endFrame, 360);
    raw.scenes[0].camera.source_end_s = 11;
    assert.throws(() => validatePlan(raw, dir, {probeMedia: false}), /shorter than the scene/);
  } finally { fs.rmSync(dir, {recursive: true, force: true}); }
});

test('ambiguous layouts and unknown plan fields fail explicitly', () => {
  const a = fixture(); a.scenes[0].cta = {text: 'TOO EARLY'};
  assert.throws(() => validatePlan(a, template), /final scene/);
  const b = fixture(); b.scenes[0].caption = 'typo';
  assert.throws(() => validatePlan(b, template), /unknown field caption/);
  const c = fixture(); c.scenes[1].id = c.scenes[0].id;
  assert.throws(() => validatePlan(c, template), /unique/);
});
