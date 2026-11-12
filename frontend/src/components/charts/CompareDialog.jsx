import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { RadarCompare } from "@/components/charts/RadarCompare";

export const CompareDialog = ({ uid, open, onClose, view }) => (
  <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
    <DialogContent className="max-w-[760px] max-h-[90vh] overflow-y-auto" style={{ background: "var(--s1)", borderColor: "var(--line)" }} data-testid="compare-dialog">
      <DialogHeader><DialogTitle>Radar Compare</DialogTitle><DialogDescription>Pick players to overlay on one radar. No real CA or PA is used.</DialogDescription></DialogHeader>
      {open && <RadarCompare ids={[uid]} view={view} />}
    </DialogContent>
  </Dialog>
);
