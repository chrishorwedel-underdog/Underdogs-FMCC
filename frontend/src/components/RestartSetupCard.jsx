import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { RotateCcw } from "lucide-react";
import { toast } from "sonner";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { api, errMsg } from "@/lib/api";

// Settings: reopen the first-run wizard to set up a different save or club.
export const RestartSetupCard = () => {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const go = async () => {
    try { await api.post("/setup/restart"); qc.invalidateQueries(); } catch (e) { toast.error(errMsg(e)); }
  };
  return (
    <div className="card rise d5" data-testid="restart-setup-card">
      <div className="ttl">Run setup again</div>
      <p className="note" style={{ marginTop: 4 }}>Reopen the setup wizard to pick a different save or club. Finishing it adds a new career; your current career and its history stay, and you can switch back in the career list above.</p>
      <button className="btn" style={{ marginTop: 8 }} onClick={() => setOpen(true)} data-testid="restart-setup-button"><RotateCcw size={14} />Run setup again</button>
      <AlertDialog open={open} onOpenChange={setOpen}>
        <AlertDialogContent data-testid="restart-setup-dialog">
          <AlertDialogHeader>
            <AlertDialogTitle>Run setup again?</AlertDialogTitle>
            <AlertDialogDescription>FMCC will show the setup wizard. Nothing is deleted. If you change your mind, press "Cancel and go back to FMCC" on the first screen.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="restart-setup-cancel">Keep using FMCC</AlertDialogCancel>
            <AlertDialogAction onClick={go} data-testid="restart-setup-confirm">Open setup</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};
