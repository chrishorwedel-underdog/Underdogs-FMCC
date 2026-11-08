import axios from "axios";

export const api = axios.create({ baseURL: `${process.env.REACT_APP_BACKEND_URL}/api` });

export const errMsg = (e) => e?.response?.data?.detail || "Something went wrong. Please try again.";

export const ago = (iso) => {
  if (!iso) return "never";
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  return `${Math.floor(s / 86400)} d ago`;
};

export const gameDate = (iso, opts = { month: "long", year: "numeric" }) =>
  iso ? new Date(`${iso}T12:00:00`).toLocaleDateString("en-GB", opts) : "";
