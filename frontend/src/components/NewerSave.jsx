import { useQuery, useQueryClient } from "@tanstack/react-query";
import { FileClock } from "lucide-react";
import { toast } from "sonner";
import { api, errMsg } from "@/lib/api";

// Banner when a newer save than the one this career follows shows up on the PC.
export const NewerSave = ({ career }) => {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["newer-saves", career.id, career.save_file], queryFn: () => api.get("/saves/newer").then((r) => r.data), refetchInterval: 120000, refetchOnWindowFocus: true });
  const s = data?.items?.[0];
  if (!s) return null;
  const follow = async () => {
    try {
      await api.put("/careers/active/folder", { save_folder: s.folder, save_file: s.path, expected_career_id: career.id });
      toast.success(`Now following ${s.name}. Press the refresh button in the top bar to read it.`);
      qc.invalidateQueries({ queryKey: ["state"] }); qc.invalidateQueries({ queryKey: ["newer-saves"] });
    } catch (e) { toast.error(errMsg(e)); }
  };
  const later = async () => {
    try { await api.post("/saves/newer/dismiss", { path: s.path, modified: s.modified }); qc.invalidateQueries({ queryKey: ["newer-saves"] }); } catch (e) { toast.error(errMsg(e)); }
  };
  const when = new Date(s.modified * 1000).toLocaleString(undefined, { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  return (
    <div className="banner rise newer-save" role="status" data-testid="newer-save-banner">
      <FileClock size={18} />
      <div style={{ flex: 1, minWidth: 0 }}><b>A newer save is on your PC: {s.name}</b>
        <small>Saved {when}. FMCC is following {data.following}.{data.items.length > 1 ? ` ${data.items.length - 1} more newer save${data.items.length > 2 ? "s" : ""} too.` : ""}</small></div>
      <button className="btn btn-p" onClick={follow} data-testid="newer-save-follow">Follow this save</button>
      <button className="btn" onClick={later} data-testid="newer-save-dismiss">Keep current</button>
    </div>
  );
};
