const KEY = "fmcc-appearance";
export const DEFAULTS = { theme: "dark", accent: "#4C8DFF", text: 115, motion: true, grain: true };
export const THEMES = {
  dark: { label: "Dark", vars: {} },
  black: { label: "Pure black", vars: { "--bg": "#000000", "--s1": "#050506", "--s2": "#0B0C0E", "--s3": "#121418" } },
  dim: { label: "Dim grey", vars: { "--bg": "#16191E", "--s1": "#1C2027", "--s2": "#232831", "--s3": "#2B313B", "--mut": "#9AA1AC" } },
  navy: { label: "Midnight blue", vars: { "--bg": "#070B16", "--s1": "#0B1222", "--s2": "#111A2E", "--s3": "#18233B" } },
};
export const ACCENTS = [["Blue", "#4C8DFF"], ["Green", "#34D399"], ["Amber", "#F2B54A"], ["Red", "#FF6E6E"], ["Purple", "#A78BFA"], ["Pink", "#F472B6"], ["Teal", "#2DD4BF"]];
export const TEXT_SIZES = [[115, "Normal"], [130, "Large"], [142.5, "Larger"], [155, "Largest"]];
const OLD_SIZES = { 100: 115, 112: 130, 125: 142.5, 140: 155 };
const ALL_VARS = ["--bg", "--s1", "--s2", "--s3", "--mut"];

export const loadAppearance = () => {
  try {
    const s = { ...DEFAULTS, ...JSON.parse(localStorage.getItem(KEY) || "{}") };
    return TEXT_SIZES.some(([v]) => v === s.text) ? s : { ...s, text: OLD_SIZES[s.text] || DEFAULTS.text };
  } catch { return DEFAULTS; }
};

export const applyAppearance = (s) => {
  const root = document.documentElement;
  ALL_VARS.forEach((v) => root.style.removeProperty(v));
  Object.entries((THEMES[s.theme] || THEMES.dark).vars).forEach(([k, v]) => root.style.setProperty(k, v));
  root.style.setProperty("--acc", s.accent);
  root.style.setProperty("--z", String(s.text / 100));
  root.style.zoom = "";
  root.classList.toggle("side-compact", s.text >= 130);
  root.classList.toggle("no-motion", !s.motion);
  root.classList.toggle("no-grain", !s.grain);
};

export const saveAppearance = (s) => {
  localStorage.setItem(KEY, JSON.stringify(s));
  applyAppearance(s);
};
