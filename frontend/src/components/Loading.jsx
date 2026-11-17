import { useEffect, useState } from "react";
import { useIsFetching, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";

const FAILED = "FMCC couldn't load this from your latest save. Try again, or read a newer save.";

const failedDetail = (qc) => {
  const q = qc.getQueryCache().findAll({ type: "active" }).find((x) => x.state.status === "error");
  const d = q?.state.error?.response?.data?.detail;
  return typeof d === "string" && d.length < 180 ? d : null;
};

// Shaped placeholder while a screen loads. If loading stops without data, or runs past 30 s, it says so with Try again instead of loading forever.
export const Loading = ({ id = "loading", rows = 4, label = "Loading" }) => {
  const qc = useQueryClient();
  const fetching = useIsFetching();
  const [since, setSince] = useState(Date.now());
  const [now, setNow] = useState(Date.now());
  useEffect(() => { const t = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(t); }, []);
  const settled = fetching === 0 && now - since > 1500;
  const slow = now - since > 30000;
  const retry = () => { setSince(Date.now()); setNow(Date.now()); qc.refetchQueries({ type: "active" }); };
  if (settled || now - since > 60000) {
    return (
      <div className="load-fail" role="alert" data-testid={`${id}-failed`}>
        <span>{failedDetail(qc) || FAILED}</span>
        <button className="btn" onClick={retry} data-testid={`${id}-retry`}><RefreshCw size={14} />Try again</button>
      </div>
    );
  }
  return (
    <div className="skel-wrap" role="status" aria-label={label} data-testid={id}>
      {slow && <p className="note" data-testid={`${id}-slow`}>Still working on it. Big saves can take a little longer.</p>}
      <div className="skel" style={{ width: "38%", height: 18 }} />
      {Array.from({ length: rows }, (_, i) => <div key={i} className="skel" style={{ width: `${92 - i * 9}%` }} />)}
    </div>
  );
};
