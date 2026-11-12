import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import { api, errMsg } from "@/lib/api";

export const useWatchlist = () => useQuery({ queryKey: ["watchlist"], queryFn: () => api.get("/watch").then((r) => r.data), staleTime: 30000 });

export const useToggleWatch = () => {
  const qc = useQueryClient();
  return async (uid, name, on) => {
    try {
      if (on) { await api.delete(`/watch/${uid}`); toast.success(`${name} removed from your watchlist`); }
      else { await api.post("/watch", { unique_id: uid }); toast.success(`Watching ${name}. You'll get a bell notice when his grade, value or contract changes.`); }
      qc.invalidateQueries({ queryKey: ["watchlist"] });
    } catch (e) { toast.error(errMsg(e)); }
  };
};

export const WatchButton = ({ uid, name, compact, id }) => {
  const { data } = useWatchlist();
  const toggle = useToggleWatch();
  const on = !!data?.ids?.includes(uid);
  const label = on ? `Stop watching ${name}` : `Watch ${name}`;
  if (compact) {
    return <button className={`ib watch-ib${on ? " on" : ""}`} style={{ width: 26, height: 26 }} onClick={(e) => { e.stopPropagation(); toggle(uid, name, on); }} title={on ? "Watching: click to stop" : "Watch: get alerts when he changes"} aria-label={label} aria-pressed={on} data-testid={id || `watch-${uid}`}>
      {on ? <Eye size={13} /> : <Eye size={13} style={{ opacity: 0.55 }} />}</button>;
  }
  return <button className={`btn${on ? " watch-on" : ""}`} onClick={() => toggle(uid, name, on)} aria-pressed={on} data-testid={id || `watch-${uid}`}>
    {on ? <><EyeOff size={13} />Watching</> : <><Eye size={13} />Watch</>}</button>;
};
