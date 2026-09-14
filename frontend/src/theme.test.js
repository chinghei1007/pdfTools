import test from "node:test";
import assert from "node:assert/strict";
import { ENGINE_COLORS, ENGINES, contrastWithWhite, deriveEngineTheme, engineColor, resolveThemePreference } from "./theme.js";

test("engine palette is stable and indexed", () => {
  assert.equal(ENGINE_COLORS.length, 10);
  assert.equal(engineColor(ENGINES[0]), "#F7C6C7");
  assert.equal(engineColor(ENGINES[1]), "#C7E8F3");
  assert.throws(() => engineColor({ colorIndex: 10 }));
});

test("derived actions use white text at AA contrast", () => {
  for (const color of ENGINE_COLORS) {
    const match = deriveEngineTheme(color).action.match(/hsl\((\d+) ([\d.]+)% ([\d.]+)%\)/);
    assert.ok(match);
    // The derivation loop itself is covered through this exported invariant.
    assert.ok(deriveEngineTheme(color).contrast >= 4.5);
  }
  assert.equal(contrastWithWhite([0, 0, 0]), 21);
});

test("Auto follows the operating system and manual themes take precedence", () => {
  assert.equal(resolveThemePreference("auto", true), "dark");
  assert.equal(resolveThemePreference("auto", false), "light");
  assert.equal(resolveThemePreference("light", true), "light");
  assert.equal(resolveThemePreference("dark", false), "dark");
  assert.equal(resolveThemePreference("invalid", true), "dark");
});
