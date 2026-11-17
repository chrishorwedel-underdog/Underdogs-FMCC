import { useState } from "react";
import { Search, FolderOpen } from "lucide-react";
import { api } from "@/lib/api";
import { useAct } from "@/lib/ui";

// "Find it automatically" and "Choose it myself" for NG_Regens faces that are already installed.
export const NgFind = ({ keys = ["extras", "editor-status"] }) => {
  const act = useAct();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState(null);
  const [choose, setChoose] = useState(false);
  const [folder, setFolder] = useState("");
  const find = async () => {
    setBusy(true);
    const r = await act(() => api.post("/editor/ng/find"), null, keys);
    setBusy(false);
    if (r) { setMsg(r.message); if (!r.found) setChoose(true); }
  };
  const pick = () => act(() => api.post("/editor/ng/choose", { folder }), (r) => `Using NG_Regens in ${r.folder}`, keys);
  return (
    <div className="ng-find" data-testid="ng-find">
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        <button className="btn" disabled={busy} onClick={find} data-testid="ng-find-auto"><Search size={13} />{busy ? "Searching…" : "Find it automatically"}</button>
        <button className="btn" onClick={() => setChoose((v) => !v)} data-testid="ng-choose-toggle"><FolderOpen size={13} />Choose it myself</button>
      </div>
      {msg && <small className="note" data-testid="ng-find-message">{msg}</small>}
      {choose && <div style={{ display: "flex", gap: 6, marginTop: 6, flexWrap: "wrap" }}>
        <input className="inp" style={{ flex: "1 1 240px" }} placeholder="e.g. C:\Users\You\Documents\Sports Interactive\Football Manager 2026\graphics\NG_Regens" value={folder} onChange={(e) => setFolder(e.target.value)} data-testid="ng-choose-input" />
        <button className="btn btn-p" disabled={folder.trim().length < 3} onClick={pick} data-testid="ng-choose-save">Use this folder</button>
      </div>}
    </div>
  );
};
