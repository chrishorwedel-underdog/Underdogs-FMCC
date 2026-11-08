import { Check, X, Download, ShieldAlert } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";

const Item = ({ it, act }) => {
  const [note, setNote] = useState(it.note || "");
  const save = (status) => act(() => api.put(`/testing/${it.key}`, { status, note }), "Saved", ["testing"]);
  return (
    <div className={`chk ${it.status === "pass" ? "ok" : it.status === "fail" ? "fail" : ""}`} style={{ alignItems: "flex-start" }} data-testid={`test-item-${it.key}`}>
      <div style={{ flex: 1 }}><b>{it.label}</b><small>{it.how}</small>
        <input className="inp" style={{ marginTop: 8, height: 34 }} placeholder="Note (optional)" maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} data-testid={`test-note-${it.key}`} /></div>
      <div style={{ display: "grid", gap: 6 }}>
        <button className={`btn${it.status === "pass" ? " btn-g" : ""}`} onClick={() => save("pass")} data-testid={`test-pass-${it.key}`}><Check size={13} />Pass</button>
        <button className={`btn${it.status === "fail" ? " btn-d" : ""}`} onClick={() => save("fail")} data-testid={`test-fail-${it.key}`}><X size={13} />Fail</button>
      </div>
    </div>
  );
};

export const TestingCard = () => {
  const { data } = useGet("testing", "/testing");
  const act = useAct();
  if (!data) return null;
  const done = data.items.filter((i) => i.status !== "untested").length;
  return (
    <div className="card rise d4" id="testing" data-testid="testing-card">
      <div className="ttl">Testing<span className="st n">{done}/{data.items.length} tried</span><span style={{ marginLeft: "auto" }} />
        <a className="btn btn-p" href={`${process.env.REACT_APP_BACKEND_URL}/api/testing/report`} data-testid="testing-export"><Download size={13} />Export report</a></div>
      <p className="note" style={{ marginTop: 6 }}>{data.desktop ? "Work through these on your PC with FM26 and FM27, then export the report and send it back. Personal folder names are hidden in the report." : "These need the Windows program on your PC. You can look through them here; results only mean something once you test on Windows."}</p>
      <div className="chk warn" style={{ marginTop: 12 }} data-testid="testing-unsigned-help"><span className="chk-i"><ShieldAlert size={16} /></span>
        <div><b>"Windows protected your PC"</b><small>The installer isn't signed yet, so Windows warns you the first time. Click More info, then Run anyway. Download FMCC-Setup.exe only from your own GitHub Actions build.</small></div></div>
      <div className="checks">{data.items.map((it) => <Item key={it.key} it={it} act={act} />)}</div>
    </div>
  );
};
