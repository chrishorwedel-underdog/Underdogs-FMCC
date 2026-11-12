import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ChevronDown, ChevronUp, History } from "lucide-react";
import { api } from "@/lib/api";
import { usePersist } from "@/lib/remember";
import { Loading } from "@/components/Loading";

const TONE = { up: "green", down: "red", info: "gold" };

const Section = ({ id, title, items }) => !items.length ? null : (
  <div className="wc-sec" data-testid={`whatchanged-${id}`}>
    <div className="eyebrow">{title} ({items.length})</div>
    {items.map((it, i) => (
      <Link key={i} to={it.to} className={`wc-row ${TONE[it.tone] || ""}`} data-testid={`whatchanged-${id}-${i}`}><i /><b>{it.name}</b><span>{it.text}</span></Link>
    ))}
  </div>
);

export const WhatChanged = () => {
  const [shut, setShut] = usePersist("digest-collapsed", false);
  const { data, isError } = useQuery({ queryKey: ["home-digest"], queryFn: () => api.get("/watch/digest").then((r) => r.data), retry: false });
  const p = (r, watch) => ({ ...r, to: watch ? `/scouting?tab=watchlist&player=${r.unique_id}` : `/squad?player=${r.unique_id}` });
  const since = data && new Date(data.since).toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" });
  return (
    <div className="card rise d3 whatchanged" data-testid="whatchanged-panel">
      <button className="guide-head" onClick={() => setShut(!shut)} aria-expanded={!shut} data-testid="whatchanged-toggle">
        <History size={15} /><b>What changed</b>
        <span style={{ color: "var(--dim)" }}>{data ? `${data.total} change${data.total === 1 ? "" : "s"} since ${since}${data.sample ? " · sample data" : ""}` : ""}</span>
        {shut ? <ChevronDown size={15} /> : <ChevronUp size={15} />}
      </button>
      {!shut && (
        <div className="wc-body" data-testid="whatchanged-body">
          {isError ? <p className="note" data-testid="whatchanged-error">Nothing to compare yet. This fills in once FMCC has read your save.</p> : !data ? <Loading id="whatchanged-loading" rows={3} label="Loading what changed" /> : !data.total ? (
            <p className="note" data-testid="whatchanged-none">Nothing changed since your last visit. Changes show up here after FMCC reads a newer save{data.compared_save ? "" : ", once it has two saves to compare"}.</p>
          ) : <>
            <Section id="ratings" title="Grades rose or fell" items={data.ratings.map((r) => p(r))} />
            <Section id="contracts" title="Contracts" items={data.contracts.map((r) => p(r))} />
            <Section id="applied" title="FMCC changes applied to the save" items={data.applied.map((g) => ({ name: `${g.label}: ${g.count}`, text: g.names.join(", "), to: g.link, tone: "info" }))} />
            <Section id="watch" title="Your watchlist" items={data.watch.map((r) => p(r, true))} />
            <small className="note">Uses FMCC grades and scouting views only. Real CA and PA are never shown. <Link to="/changes" style={{ color: "var(--acc)" }} data-testid="whatchanged-all-changes">See every change in Game changes</Link></small>
          </>}
        </div>
      )}
    </div>
  );
};
