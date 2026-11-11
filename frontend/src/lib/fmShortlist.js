import { api } from "@/lib/api";

export const sendToFm = (act, ids) => act(() => api.post("/scouting/send-to-fm", { ids }),
  (r) => (r.queued ? `${r.queued} player(s) queued for your FM shortlist. Apply them in Game changes.` : "Already queued or sent to your FM shortlist")
    + (r.queued && r.already ? ` ${r.already} were already there.` : ""), ["changes"]);
