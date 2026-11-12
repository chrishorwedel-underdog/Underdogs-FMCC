import { createContext, useContext } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useLocation } from "react-router-dom";
import { api, errMsg } from "@/lib/api";
import { GUIDES } from "@/constants/guides";
import { GuideLink } from "@/components/ModuleGuide";

// Pages shown inside a Settings section render a small section heading instead of a full page head.
export const EmbedCtx = createContext(false);

export const useGet = (key, url, params, opts = {}) =>
  useQuery({ queryKey: [key, params], queryFn: () => api.get(url, { params }).then((r) => r.data), ...opts });

export const useAct = () => {
  const qc = useQueryClient();
  return async (fn, ok, keys) => {
    try {
      const { data } = await fn();
      if (ok) toast.success(typeof ok === "function" ? ok(data) : ok);
      keys ? keys.forEach((k) => qc.invalidateQueries({ queryKey: [k] })) : qc.invalidateQueries();
      return data;
    } catch (e) {
      toast.error(errMsg(e));
      return null;
    }
  };
};

export const TabBar = ({ tabs, value, onChange, id }) => (
  <div className="seg" data-testid={`${id}-tabs`}>
    {tabs.map(([k, l]) => <button key={k} className={value === k ? "on" : ""} onClick={() => onChange(k)} data-testid={`${id}-tab-${k}`}>{l}</button>)}
  </div>
);

export const PageHead = ({ eyebrow, title, purpose, children }) => {
  const { pathname } = useLocation();
  const embedded = useContext(EmbedCtx);
  const line = purpose ?? GUIDES[pathname]?.what;
  if (embedded) {
    return <div className="sec-head"><h2 data-testid="section-title">{title}</h2>{children && <div style={{ marginLeft: "auto", display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>{children}</div>}</div>;
  }
  return (
    <div className="head rise">
      <div style={{ minWidth: 0 }}><div className="eyebrow">{eyebrow}</div><div className="h-row"><h1 className="h">{title}</h1><GuideLink /></div>
        {line && <p className="purpose" data-testid="page-purpose">{line}</p>}</div>
      {children && <div style={{ marginLeft: "auto", display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>{children}</div>}
    </div>
  );
};

export const money = (v) => (v >= 1e6 ? `£${(v / 1e6).toFixed(1)}m` : `£${Math.round(v / 1000)}k`);
