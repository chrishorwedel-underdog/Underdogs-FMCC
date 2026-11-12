import { useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useLocation } from "react-router-dom";
import { api, errMsg } from "@/lib/api";
import { GUIDES } from "@/constants/guides";

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
  const line = purpose ?? GUIDES[pathname]?.what;
  return (
    <div className="head rise">
      <div style={{ minWidth: 0 }}><div className="eyebrow">{eyebrow}</div><h1 className="h">{title}</h1>
        {line && <p className="purpose" data-testid="page-purpose">{line}</p>}</div>
      {children && <div style={{ marginLeft: "auto", display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>{children}</div>}
    </div>
  );
};

export const money = (v) => (v >= 1e6 ? `£${(v / 1e6).toFixed(1)}m` : `£${Math.round(v / 1000)}k`);
