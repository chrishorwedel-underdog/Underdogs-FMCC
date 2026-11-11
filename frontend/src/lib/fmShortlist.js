import { api } from "@/lib/api";

const were = (n) => `${n} ${n === 1 ? "was" : "were"} already there.`;

export const sendToFm = (act, ids) => act(() => api.post("/scouting/send-to-fm", { ids }),
  (r) => (r.queued ? `${r.queued} player${r.queued === 1 ? "" : "s"} queued for your FM shortlist. Apply them in Game changes.` : "Already queued or sent to your FM shortlist")
    + (r.queued && r.already ? ` ${were(r.already)}` : ""), ["changes"]);
