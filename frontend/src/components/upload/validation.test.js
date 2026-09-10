import test from "node:test";
import assert from "node:assert/strict";
import { validateFiles } from "./validation.js";

test("accepts case-insensitive extensions and MIME wildcards with empty MIME fallback", () => {
  const files = [
    { name: "FILE.PDF", type: "", size: 1 },
    { name: "photo.png", type: "image/png", size: 2 },
  ];
  assert.deepEqual(validateFiles(files, { accept: ".pdf,image/*" }), {
    accepted: files,
    errors: [],
  });
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
