import test from "node:test";
import assert from "node:assert/strict";
import { validateFiles } from "./validation.js";

test('tool categories reject the opposite category and contradictory MIME', () => {
  const pdf = { name: 'a.pdf', type: 'application/pdf', size: 10 };
  const image = { name: 'a.png', type: 'image/png', size: 10 };
  assert.deepEqual(validateFiles([pdf, image], { type: 'pdf' }).accepted, [pdf]);
  assert.deepEqual(validateFiles([pdf, image], { type: 'image' }).accepted, [image]);
  assert.equal(validateFiles([{ ...pdf, type: 'image/png' }], { type: 'pdf' }).errors.length, 1);
  assert.equal(validateFiles([{ ...pdf, type: '' }], { type: 'pdf' }).accepted.length, 1);
  assert.equal(validateFiles([{ ...pdf, size: 0 }], { type: 'pdf' }).errors.length, 1);
});

test("accepts case-insensitive extensions and MIME wildcards with empty MIME fallback", () => {
  const files = [
    { name: "FILE.PDF", type: "", size: 1 },
    { name: "photo.png", type: "image/png", size: 2 },
  ];
  assert.deepEqual(validateFiles(files, { accept: ".pdf,image/*" }), {
    accepted: files,
    errors: [],
    issues: [],
  });
});
test('zero-byte handoffs report a diagnostic without rejecting a nonempty PDF', () => {
  const empty = new File([], 'document.pdf', { type: 'application/pdf' });
  const nonempty = new File(['%PDF-1.7'], 'document.pdf', { type: 'application/pdf' });
  const result = validateFiles([empty, nonempty], { type: 'pdf' });
  assert.deepEqual(result.accepted, [nonempty]);
  assert.equal(result.issues[0].code, 'zero_bytes');
  assert.equal(result.issues[0].sizeBytes, 0);
  assert.match(result.errors[0], /browser received 0 bytes/);
});
test("rejects oversized and unsupported files without rejecting valid siblings", () => {
  const valid = { name: "ok.pdf", type: "application/pdf", size: 10 };
  const result = validateFiles(
    [
      valid,
      { ...valid, name: "large.pdf", size: 11 },
      { name: "bad.exe", type: "", size: 1 },
    ],
    { accept: ".pdf", maxSizeBytes: 10 },
  );
  assert.deepEqual(result.accepted, [valid]);
  assert.equal(result.errors.length, 2);
});
test("single selection accepts only the first valid file", () => {
  const files = [
    { name: "a.pdf", type: "", size: 1 },
    { name: "b.pdf", type: "", size: 1 },
  ];
  const result = validateFiles(files, { multiple: false });
  assert.deepEqual(result.accepted, [files[0]]);
  assert.equal(result.errors.length, 1);
});
