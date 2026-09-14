export const ENGINE_COLORS = [
  "#F7C6C7",
  "#C7E8F3",
  "#F9E2B7",
  "#F5D1E8",
  "#D4E7D9",
  "#D6D8F6",
  "#F8D7B9",
  "#F3CFCF",
  "#F7E4D8",
  "#CFE6F1",
];

export const ENGINES = [
  { id: "pypdf", label: "pypdf", colorIndex: 0 },
  { id: "pymupdf", label: "PyMuPDF", colorIndex: 1 },
];

export function engineColor(engine) {
  if (!Number.isInteger(engine?.colorIndex) || engine.colorIndex < 0 || engine.colorIndex >= ENGINE_COLORS.length) {
    throw new Error("Engine colorIndex must be an integer from 0 through 9.");
  }
  return ENGINE_COLORS[engine.colorIndex];
}

function hexToRgb(hex) {
  const value = Number.parseInt(hex.slice(1), 16);
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}

function rgbToHsl([red, green, blue]) {
  const [r, g, b] = [red, green, blue].map((value) => value / 255);
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const lightness = (max + min) / 2;
  if (max === min) return [0, 0, lightness * 100];
  const delta = max - min;
  const saturation = delta / (1 - Math.abs(2 * lightness - 1));
  let hue = max === r ? ((g - b) / delta) % 6 : max === g ? (b - r) / delta + 2 : (r - g) / delta + 4;
  hue = Math.round(hue * 60);
  if (hue < 0) hue += 360;
  return [hue, saturation * 100, lightness * 100];
}

function hslToRgb([hue, saturation, lightness]) {
  const s = saturation / 100;
  const l = lightness / 100;
  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs(((hue / 60) % 2) - 1));
  const m = l - c / 2;
  const [r, g, b] = hue < 60 ? [c, x, 0] : hue < 120 ? [x, c, 0] : hue < 180 ? [0, c, x] : hue < 240 ? [0, x, c] : hue < 300 ? [x, 0, c] : [c, 0, x];
  return [r, g, b].map((value) => Math.round((value + m) * 255));
}

function luminance(rgb) {
  const values = rgb.map((value) => {
    const channel = value / 255;
    return channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  });
  return values[0] * 0.2126 + values[1] * 0.7152 + values[2] * 0.0722;
}

export function contrastWithWhite(rgb) {
  return 1.05 / (luminance(rgb) + 0.05);
}

export function deriveEngineTheme(base) {
  const [hue, saturation, lightness] = rgbToHsl(hexToRgb(base));
  const actionSaturation = Math.min(100, saturation + 10);
  let actionLightness = Math.max(0, lightness - 30);
  while (actionLightness > 0 && contrastWithWhite(hslToRgb([hue, actionSaturation, actionLightness])) < 4.5) {
    actionLightness -= 1;
  }
  const contrast = contrastWithWhite(hslToRgb([hue, actionSaturation, actionLightness]));
  return {
    base,
    surface: base,
    action: `hsl(${hue} ${actionSaturation.toFixed(1)}% ${actionLightness.toFixed(1)}%)`,
    hover: `hsl(${hue} ${actionSaturation.toFixed(1)}% ${Math.max(0, actionLightness - 6).toFixed(1)}%)`,
    text: "#ffffff",
    contrast,
  };
}

export function applyEngineTheme(element, engine) {
  const theme = deriveEngineTheme(engineColor(engine));
  element.style.setProperty("--pdf-engine-color", theme.base);
  element.style.setProperty("--pdf-engine-surface", theme.surface);
  element.style.setProperty("--pdf-action-color", theme.action);
  element.style.setProperty("--pdf-action-hover", theme.hover);
  element.style.setProperty("--pdf-action-text", theme.text);
  element.dataset.engine = engine.id;
  return theme;
}

export function resolveThemePreference(selection, systemDark) {
  if (!["auto", "light", "dark"].includes(selection)) return systemDark ? "dark" : "light";
  return selection === "auto" ? (systemDark ? "dark" : "light") : selection;
}
