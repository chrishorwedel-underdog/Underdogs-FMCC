import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { KeyRound, Loader2 } from "lucide-react";
import { api, errMsg } from "@/lib/api";

// Shown on the chat page while no working OpenAI key is connected.
export const DofKeyBox = ({ desktop }) => {
  const qc = useQueryClient();
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const go = async () => {
    setBusy(true); setErr(null);
    try {
      const { data } = await api.post("/setup/check-key", { key: desktop ? key.trim() : null });
      if (data.ok) { setKey(""); qc.invalidateQueries({ queryKey: ["dof-status"] }); } else setErr(data.error);
    } catch (e) { setErr(errMsg(e)); } finally { setBusy(false); }
  };
  return (
    <div className="card" style={{ marginBottom: 16 }} data-testid="dof-key-box">
      <div className="ttl"><KeyRound size={15} />Connect your OpenAI key</div>
      <p className="note" style={{ marginTop: 6 }}>FMCC checks the key, picks the best chat model your account can use and saves the key only on this PC.</p>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 10 }}>
        <input className="inp mono" style={{ flex: "1 1 260px" }} type="password" placeholder="sk-..." value={key} onChange={(e) => setKey(e.target.value)} data-testid="dof-key-input" />
        <button className="btn btn-p" disabled={busy || (desktop && key.trim().length < 20)} onClick={go} data-testid="dof-key-connect">{busy ? <Loader2 size={14} className="animate-spin" /> : null}Check and connect</button>
      </div>
      {err && <p className="chk-fix" style={{ marginTop: 8 }} data-testid="dof-key-error">{err}</p>}
    </div>
  );
};
