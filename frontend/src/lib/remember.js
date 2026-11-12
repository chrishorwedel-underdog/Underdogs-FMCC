import { useEffect, useLayoutEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export const useCareerId = () => {
  const { data } = useQuery({ queryKey: ["state"], queryFn: () => api.get("/state").then((r) => r.data) });
  return data?.career?.id || null;
};

const keyOf = (cid, key) => `fmcc-mem:${cid}:${key}`;
const read = (cid, key, initial) => {
  const fallback = typeof initial === "function" ? initial() : initial;
  if (!cid) return fallback;
  try {
    const v = localStorage.getItem(keyOf(cid, key));
    return v == null ? fallback : JSON.parse(v);
  } catch { return fallback; }
};

// useState that is remembered per career on this computer.
export const usePersist = (key, initial) => {
  const cid = useCareerId();
  const [v, setV] = useState(() => read(cid, key, initial));
  useEffect(() => { setV(read(cid, key, initial)); }, [cid, key]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    const on = (e) => { if (e.detail === keyOf(cid, key)) { setV(read(cid, key, initial)); } };
    window.addEventListener("fmcc-mem", on);
    return () => { window.removeEventListener("fmcc-mem", on); };
  }, [cid, key]); // eslint-disable-line react-hooks/exhaustive-deps
  const set = (n) => setV((old) => {
    const val = typeof n === "function" ? n(old) : n;
    if (cid) { localStorage.setItem(keyOf(cid, key), JSON.stringify(val)); setTimeout(() => window.dispatchEvent(new CustomEvent("fmcc-mem", { detail: keyOf(cid, key) })), 0); }
    return val;
  });
  return [v, set];
};

const scroller = () => document.querySelector(".content");

export const ScrollMemory = () => {
  const { pathname, search } = useLocation();
  const cid = useCareerId();
  const key = `scroll:${pathname}${search}`;
  useLayoutEffect(() => {
    if (!cid) { return undefined; }
    const el = scroller();
    const want = Number(localStorage.getItem(keyOf(cid, key)) || 0);
    const timers = [80, 400, 1200].map((ms) => setTimeout(() => { if (el && want && el.scrollTop < want) el.scrollTop = want; }, ms));
    let t;
    const save = () => { clearTimeout(t); t = setTimeout(() => localStorage.setItem(keyOf(cid, key), String(el.scrollTop)), 150); };
    el?.addEventListener("scroll", save, { passive: true });
    return () => { timers.forEach(clearTimeout); el?.removeEventListener("scroll", save); };
  }, [cid, key]);
  return null;
};

// After a dossier closes, bring the same player's row back into view and flash it.
export const returnToRow = (uid) => {
  setTimeout(() => {
    const row = document.querySelector(`[data-row-uid="${uid}"]`);
    if (!row) { return; }
    row.scrollIntoView({ block: "center" });
    row.classList.add("row-flash");
    row.focus?.({ preventScroll: true });
    setTimeout(() => row.classList.remove("row-flash"), 1600);
  }, 120);
};
