import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { api, errMsg, gameDate } from "@/lib/api";

const NewCareer = ({ open, setOpen }) => {
  const qc = useQueryClient();
  const [f, setF] = useState({ name: "", club_name: "", edition: "FM27" });
  const [busy, setBusy] = useState(false);
  const save = async () => {
    setBusy(true);
    try { await api.post("/careers", f); toast.success("Career created and first save read"); setOpen(false); setF({ name: "", club_name: "", edition: "FM27" }); qc.invalidateQueries(); } catch (e) { toast.error(errMsg(e)); } finally { setBusy(false); }
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent data-testid="new-career-dialog">
        <DialogHeader><DialogTitle>New career</DialogTitle><DialogDescription>Each career keeps its own club, seasons and history.</DialogDescription></DialogHeader>
        <label className="lbl">Career name</label><input className="inp" maxLength={60} value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} data-testid="new-career-name" />
        <label className="lbl">Club</label><input className="inp" maxLength={60} value={f.club_name} onChange={(e) => setF({ ...f, club_name: e.target.value })} data-testid="new-career-club" />
        <div className="seg">{["FM26", "FM27"].map((e) => <button key={e} className={f.edition === e ? "on" : ""} onClick={() => setF({ ...f, edition: e })} data-testid={`new-career-${e.toLowerCase()}`}>{e}</button>)}</div>
        <button className="btn btn-p btn-l" disabled={busy || !f.name.trim() || !f.club_name.trim()} onClick={save} data-testid="new-career-save">Create career</button>
      </DialogContent>
    </Dialog>
  );
};

export const CareersCard = ({ career }) => {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [folder, setFolder] = useState(career.save_folder);
  const { data = [] } = useQuery({ queryKey: ["careers"], queryFn: () => api.get("/careers").then((r) => r.data) });
  const activate = async (id) => {
    try { await api.post(`/careers/${id}/activate`); toast.success("Career switched"); qc.invalidateQueries(); } catch (e) { toast.error(errMsg(e)); }
  };
  const saveFolder = async () => {
    try { await api.put("/careers/active/folder", { save_folder: folder, expected_career_id: career.id }); toast.success("Save folder updated"); qc.invalidateQueries({ queryKey: ["state"] }); } catch (e) { toast.error(errMsg(e)); }
  };
  return (
    <div className="card rise d1" data-testid="careers-card">
      <div className="ttl">Careers<span style={{ marginLeft: "auto" }} /><button className="btn" onClick={() => setOpen(true)} data-testid="new-career-button"><Plus size={14} />New career</button></div>
      {data.map((c) => (
        <div className="row" key={c.id} data-testid={`career-row-${c.id}`}>
          <div style={{ flex: 1 }}><b>{c.name}</b><small>{c.club_name} · {c.edition} · {gameDate(c.last_game_date)} · {c.next_save_no} {c.next_save_no === 1 ? "save" : "saves"} read</small></div>
          {c.active ? <span className="st ok">Active</span> : <button className="btn" onClick={() => activate(c.id)} data-testid={`career-activate-${c.id}`}>Switch</button>}
        </div>
      ))}
      <label className="lbl" style={{ marginTop: 14 }}>Save folder for {career.name}</label>
      <div style={{ display: "flex", gap: 8 }}>
        <input className="inp mono" style={{ fontSize: 12.5 }} value={folder} onChange={(e) => setFolder(e.target.value)} data-testid="save-folder-input" />
        <button className="btn" style={{ height: 40 }} disabled={folder.trim().length < 3 || folder === career.save_folder} onClick={saveFolder} data-testid="save-folder-save">Save</button>
      </div>
      <NewCareer open={open} setOpen={setOpen} />
    </div>
  );
};
