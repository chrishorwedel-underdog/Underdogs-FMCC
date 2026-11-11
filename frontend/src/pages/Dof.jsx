import { useEffect, useRef, useState } from "react";
import { Plus, Send, Check, X, Star, UserRound } from "lucide-react";
import { toast } from "sonner";
import { api, ago, errMsg } from "@/lib/api";
import { useGet, useAct, PageHead } from "@/lib/ui";
import { useAddress } from "@/lib/address";

const visible = (t) => { const i = t.indexOf("ACTION:"); return i >= 0 ? t.slice(0, i) : t; };

const Suggestions = ({ m, act }) => (
  <div className="sugg" data-testid={`suggestions-${m.id}`}>
    {m.draft.action.items.map((it) => (
      <div key={it.unique_id} className="sugg-c" data-testid={`suggestion-${it.unique_id}`}>
        <span className="gap">{it.gap || "Suggestion"}</span>
        <b style={{ fontSize: 14.5 }}>{it.name}<small style={{ color: "var(--mut)", fontWeight: 400 }}> · {it.club} · age {it.age}</small></b>
        <span>{it.reason}</span>
        {it.numbers && <small className="mono" style={{ color: "var(--mut)" }}>{it.numbers}</small>}
        <small className="mono">Grade {it.grade ?? "–"} · value £{(it.value || 0).toLocaleString()} · wage £{(it.wage || 0).toLocaleString()}/wk</small>
        {it.over_budget && <span className="st a" style={{ margin: 0 }} data-testid={`suggestion-over-budget-${it.unique_id}`}>Over your transfer budget</span>}
        <div className="acts">
          {it.shortlisted ? <span className="st ok" style={{ margin: 0 }} data-testid={`suggestion-shortlisted-${it.unique_id}`}>On your shortlist</span>
            : <button className="btn btn-p" style={{ whiteSpace: "nowrap" }} onClick={() => act(() => api.post(`/dof/messages/${m.id}/shortlist/${it.unique_id}`), (r) => r.result, ["dof-msgs", "scout-players", "shortlist"])} data-testid={`suggestion-shortlist-${it.unique_id}`}><Star size={13} />Add to shortlist</button>}
          <a className="btn" href={`/scouting?player=${it.unique_id}`} data-testid={`suggestion-profile-${it.unique_id}`}><UserRound size={13} />Open profile</a>
        </div>
      </div>))}
  </div>
);

const Draft = ({ m, act }) => {
  const d = m.draft;
  if (!d) return null;
  if (d.action.type === "suggestions") return <div style={{ marginTop: 10 }} data-testid={`draft-${m.id}`}><b style={{ fontSize: 13.5 }}>{d.action.summary}</b><Suggestions m={m} act={act} /></div>;
  return (
    <div className="card" style={{ marginTop: 10, padding: 14, borderColor: "rgba(76,141,255,.4)" }} data-testid={`draft-${m.id}`}>
      <div className="eyebrow">Drafted action · {d.action.type}</div>
      <p className="sent">{d.action.summary || "Suggested action"}</p>
      {d.status === "pending" ? <div className="acts">
        <button className="btn btn-p" onClick={() => act(() => api.post(`/dof/messages/${m.id}/accept`), (r) => r.result, ["dof-msgs", "plan", "rankings", "elite", "breakout", "development"])} data-testid={`draft-accept-${m.id}`}><Check size={13} />Accept</button>
        <button className="btn" onClick={() => act(() => api.post(`/dof/messages/${m.id}/dismiss`), "Dismissed", ["dof-msgs"])} data-testid={`draft-dismiss-${m.id}`}><X size={13} />Dismiss</button></div>
        : <span className={`st ${d.status === "accepted" ? "ok" : "n"}`} style={{ margin: 0 }} data-testid={`draft-status-${m.id}`}>{d.status === "accepted" ? d.result || "Accepted" : "Dismissed"}</span>}
    </div>
  );
};

const Thread = ({ conv, status, onDone }) => {
  const address = useAddress();
  const { data: msgs = [], refetch } = useGet("dof-msgs", `/dof/conversations/${conv}/messages`, { conv });
  const act = useAct();
  const [text, setText] = useState("");
  const [live, setLive] = useState(null);
  const end = useRef();
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, live]);
  const ask = async (q) => {
    if (!q.trim() || live) return;
    setText(""); setLive({ q, a: "" });
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/dof/conversations/${conv}/stream`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: q }) });
      if (!res.ok) throw new Error((await res.json()).detail);
      const reader = res.body.getReader(), dec = new TextDecoder();
      let buf = "", acc = "";
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const parts = buf.split("\n\n"); buf = parts.pop();
        for (const p of parts) {
          if (!p.startsWith("data: ")) continue;
          const ev = JSON.parse(p.slice(6));
          if (ev.t === "delta") { acc += ev.c; setLive({ q, a: acc }); }
          if (ev.t === "error") toast.error(ev.c);
        }
      }
    } catch (e) { toast.error(e.message || errMsg(e)); }
    await refetch(); setLive(null); onDone();
  };
  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 230px)", minHeight: 480 }} data-testid="dof-thread">
      <div style={{ flex: 1, overflowY: "auto", paddingRight: 6 }}>
        {msgs.length === 0 && !live && <p className="note" data-testid="dof-welcome">Ask me anything about your squad, plans, matches or transfers, {address}.</p>}
        {msgs.map((m) => <div key={m.id} className={`msg ${m.role}`} data-testid={`dof-msg-${m.role}`}><div className="bubble">{m.content}</div>{m.role === "assistant" && <Draft m={m} act={act} />}</div>)}
        {live && <><div className="msg user"><div className="bubble">{live.q}</div></div>
          <div className="msg assistant" data-testid="dof-live"><div className="bubble">{live.a ? visible(live.a) : <span className="typing" data-testid="dof-typing"><i /><i /><i /></span>}</div></div></>}
        <div ref={end} />
      </div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", margin: "12px 0 10px" }}>
        {status?.suggested.map((s, i) => <button key={s} className="btn" style={{ height: 28, fontSize: 12 }} disabled={!!live} onClick={() => ask(s)} data-testid={`dof-suggest-${i}`}>{s}</button>)}
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <input className="inp" placeholder="Ask your DOF…" value={text} maxLength={2000} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === "Enter" && ask(text)} disabled={!!live} data-testid="dof-input" />
        <button className="btn btn-p" style={{ height: 40 }} disabled={!text.trim() || !!live} onClick={() => ask(text)} data-testid="dof-send"><Send size={14} /></button>
      </div>
    </div>
  );
};

export default function Dof() {
  const { data: status } = useGet("dof-status", "/dof/status");
  const { data: convs = [], refetch: refetchConvs } = useGet("dof-convs", "/dof/conversations");
  const act = useAct();
  const [conv, setConv] = useState(null);
  useEffect(() => { if (!conv && convs.length) setConv(convs[0].id); }, [convs, conv]);
  const create = async () => { const c = await act(() => api.post("/dof/conversations", {}), null, ["dof-convs"]); if (c) setConv(c.id); };
  return (
    <div data-testid="dof-page">
      <PageHead eyebrow={status ? `${status.model} · ${status.key_source}` : ""} title="Chat with your Director of Football">
        <button className="btn btn-p" onClick={create} data-testid="dof-new-conversation"><Plus size={13} />New conversation</button>
      </PageHead>
      {status && !status.ready && <div className="banner" style={{ marginBottom: 16 }}>Add your OpenAI key in Settings to use the DOF chat.</div>}
      <div className="homegrid" style={{ gridTemplateColumns: "260px minmax(0,1fr)" }}>
        <div className="card" style={{ padding: 8, alignSelf: "start" }} data-testid="dof-conversations">
          {convs.length === 0 && <p className="note" style={{ padding: 8 }}>No conversations yet.</p>}
          {convs.map((c) => <div key={c.id} className={`pi${c.id === conv ? " sel" : ""}`} onClick={() => setConv(c.id)} data-testid={`dof-conv-${c.id}`}><span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{c.title}</span><small>{ago(c.updated_at)}</small></div>)}
        </div>
        {conv ? <Thread key={conv} conv={conv} status={status} onDone={refetchConvs} /> : <div className="soon">Start a new conversation to talk to your Director of Football.</div>}
      </div>
    </div>
  );
}
