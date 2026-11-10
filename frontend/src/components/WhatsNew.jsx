import { useQueryClient } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { useGet } from "@/lib/ui";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";

export const WhatsNew = () => {
  const qc = useQueryClient();
  const { data } = useGet("whats-new", "/fmcc/whats-new", undefined, { staleTime: Infinity });
  const close = () => {
    api.post("/fmcc/whats-new/seen").finally(() => qc.setQueryData(["whats-new", undefined], { show: false }));
  };
  return (
    <Dialog open={!!data?.show} onOpenChange={(o) => { if (!o) close(); }}>
      <DialogContent data-testid="whats-new-dialog">
        <DialogHeader>
          <DialogTitle style={{ display: "flex", alignItems: "center", gap: 8 }}><Sparkles size={18} />What's new in FMCC {data?.version}</DialogTitle>
          <DialogDescription>FMCC has just been updated. Here's what changed.</DialogDescription>
        </DialogHeader>
        {data?.items?.length ? <ul className="wn-list" data-testid="whats-new-list">{data.items.map((t) => <li key={t}>{t}</li>)}</ul>
          : <p className="note" data-testid="whats-new-empty">The list of changes couldn't be loaded right now.</p>}
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          {data?.url && <a className="btn" href={data.url} target="_blank" rel="noreferrer" data-testid="whats-new-full-notes">Full release notes</a>}
          <button className="btn btn-g" onClick={close} data-testid="whats-new-close">Got it</button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
