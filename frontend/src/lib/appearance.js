const KEY = "fmcc-appearance";
export const DEFAULTS = { theme: "dark", accent: "#4C8DFF", text: 100, motion: true, grain: true };
export const THEMES = {
  dark: { label: "Dark", vars: {} },
  black: { label: "Pure black", vars: { "--bg": "#000000", "--s1": "#050506", "--s2": "#0B0C0E", "--s3": "#121418" } },
  dim: { label: "Dim grey", vars: { "--bg": "#16191E", "--s1": "#1C2027", "--s2": "#232831", "--s3": "#2B313B", "--mut": "#9AA1AC" } },
  navy: { label: "Midnight blue", vars: { "--bg": "#070B16", "--s1": "#0B1222", "--s2": "#111A2E", "--s3": "#18233B" } },
};
export const ACCENTS = [["Blue", "#4C8DFF"], ["Green", "#34D399"], ["Amber", "#F2B54A"], ["Red", "#FF6E6E"], ["Purple", "#A78BFA"], ["Pink", "#F472B6"], ["Teal", "#2DD4BF"]];
export const TEXT_SIZES = [[100, "Normal"], [112, "Large"], [125, "Larger"], [140, "Largest"]];
const NEW_SIZES = { 115: 100, 130: 112, 142.5: 125, 155: 140 };
const ALL_VARS = ["--bg", "--s1", "--s2", "--s3", "--mut"];

export const loadAppearance = () => {
  try {
    const s = { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) || "{}") };
    return TEXT_SIZES.some(([v]) => v === s.text) ? s : { ...s, text: NEW_SIZES[s.text] || DEFAULTS.text };
  } catch { return DEFAULTS; }
};

export const applyAppearance = (s) => {
  const root = document.documentElement;
  ALL_VARS.forEach((v) => root.style.removeProperty(v));
  Object.entries((THEMES[s.theme] || THEMES.dark).vars).forEach(([k, v]) => root.style.setProperty(k, v));
  root.style.setProperty("--acc", s.accent);
  root.style.setProperty("--z", String(s.text / 100));
  root.style.zoom = "";
  root.classList.toggle("no-motion", !s.motion);
  root.classList.toggle("no-grain", !s.grain);
};

export const saveAppearance = (s) => {
  localStorage.setItem(KEY, JSON.stringify(s));
  applyAppearance(s);
};
