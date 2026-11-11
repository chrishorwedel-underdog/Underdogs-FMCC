const KEY = "fmcc-appearance";
export const DEFAULTS = { theme: "dark", accent: "#4C8DFF", text: 100, motion: true, grain: true };
export const THEMES = {
  dark: { label: "Dark", vars: {} },
  black: { label: "Pure black", vars: { "--bg": "#000000", "--s1": "#050506", "--s2": "#0B0C0E", "--s3": "#121418" } },
  dim: { label: "Dim grey", vars: { "--bg": "#16191E", "--s1": "#1C2027", "--s2": "#232831", "--s3": "#2B313B", "--mut": "#9AA1AC" } },
  navy: { label: "Midnight blue", vars: { "--bg": "#070B16", "--s1": "#0B1222", "--s2": "#111A2E", "--s3": "#18233B" } },
  light: { label: "Light", light: true, accent: "#2F6FE4", vars: { "--bg": "#FFFFFF", "--s1": "#F3F4F6", "--s2": "#F8F9FA", "--s3": "#E7E9ED", "--text": "#15181D", "--mut": "#3F4552", "--dim": "#5B6270",
    "--line": "rgba(0,0,0,.09)", "--line2": "rgba(0,0,0,.16)", "--top": "rgba(255,255,255,.85)", "--grn": "#0E9F6E", "--amb": "#B7791F", "--red": "#D64545", "--blu": "#2F6FE4" } },
  fm24: { label: "FM24", accent: "#3DDC84", vars: { "--bg": "#0E1726", "--s1": "#132033", "--s2": "#1A2940", "--s3": "#22344F", "--mut": "#9AA9BF", "--top": "rgba(14,23,38,.85)" } },
  fm26: { label: "FM26", accent: "#E05CFF", vars: { "--bg": "#150B24", "--s1": "#1C0F31", "--s2": "#24153F", "--s3": "#2E1B4F", "--mut": "#B3A3CC", "--top": "rgba(21,11,36,.85)" } },
  fm27: { label: "FM27", accent: "#A98BFF", vars: { "--bg": "#141418", "--s1": "#1A1A20", "--s2": "#212129", "--s3": "#2A2A34", "--mut": "#A5A5B4", "--top": "#2A2240" } },
};
export const ACCENTS = [["Blue", "#4C8DFF"], ["Green", "#34D399"], ["Amber", "#F2B54A"], ["Red", "#FF6E6E"], ["Purple", "#A78BFA"], ["Pink", "#F472B6"], ["Teal", "#2DD4BF"]];
export const TEXT_SIZES = [[100, "Normal"], [112, "Large"], [125, "Larger"], [140, "Largest"]];
const NEW_SIZES = { 115: 100, 130: 112, 142.5: 125, 155: 140 };
const ALL_VARS = ["--bg", "--s1", "--s2", "--s3", "--mut", "--text", "--dim", "--line", "--line2", "--top", "--grn", "--amb", "--red", "--blu"];

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
  root.classList.toggle("theme-light", !!(THEMES[s.theme] || {}).light);
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
