import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { FolderSearch, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { api, errMsg } from "@/lib/api";
import { SaveList } from "@/pages/Setup";

// Settings: scan this PC again and choose which save FMCC follows for this career.
export const SavePicker = ({ career }) => {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [saves, setSaves] = useState(null);
  const [pick, setPick] = useState(null);
  const [check, setCheck] = useState(null);
  const scan = async () => {
    setBusy(true); setCheck(null);
    try {
      const { data } = await api.post("/setup/inspect", { edition: career.edition });
      setSaves(data.saves || []);
      setPick((data.saves || []).find((s) => s.path === career.save_file) || null);
    } catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  const test = async () => {
    setCheck({ busy: true });
    try { const { data } = await api.post("/setup/check-save", { path: pick.path }); setCheck(data); } catch (e) { setCheck({ ok: false, error: errMsg(e) }); }
  };
  const use = async () => {
    try {
      await api.put("/careers/active/folder", { save_folder: pick.folder, save_file: pick.path, expected_career_id: career.id });
      toast.success(`FMCC now follows ${pick.name}. Press the refresh button in the top bar to read it.`);
      qc.invalidateQueries({ queryKey: ["state"] }); setOpen(false);
    } catch (e) { toast.error(errMsg(e)); }
  };
  const following = career.save_file ? career.save_file.split(/[\\/]/).pop().replace(/\.fm$/i, "") : null;
  return (
    <div style={{ marginTop: 14 }} data-testid="save-picker">
      <label className="lbl">Save FMCC follows</label>
      <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
        <span data-testid="save-picker-current">{following ? <b>{following}</b> : <span className="note">The newest save in the folder above</span>}</span>
        <button className="btn" style={{ marginLeft: "auto" }} onClick={() => { setOpen(!open); if (!saves) scan(); }} data-testid="save-picker-open">
          {busy ? <Loader2 size={14} className="animate-spin" /> : <FolderSearch size={14} />}Change save</button>
      </div>
      {open && saves && <div style={{ marginTop: 10 }}>
        {saves.length ? <SaveList saves={saves} pick={pick?.path} onPick={(s) => { setPick(s); setCheck(null); }} /> : <p className="note" data-testid="save-picker-none">No saves found on this PC. Type the folder above and press Save instead.</p>}
        <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap", alignItems: "center" }}>
          <button className="btn" onClick={scan} disabled={busy} data-testid="save-picker-rescan">Scan again</button>
          <button className="btn" onClick={test} disabled={!pick || check?.busy} data-testid="save-picker-check">{check?.busy ? "Reading the save\u2026" : "Check this save"}</button>
          <button className="btn btn-p" onClick={use} disabled={!pick || pick.path === career.save_file || check?.ok === false} data-testid="save-picker-use">Follow this save</button>
          {check?.ok && <span className="st ok" data-testid="save-picker-ok">Read OK: {check.club_name}, {check.players} players</span>}
        </div>
        {check?.ok === false && <p className="chk-fix" data-testid="save-picker-error">{check.error}</p>}
      </div>}
    </div>
  );
};
