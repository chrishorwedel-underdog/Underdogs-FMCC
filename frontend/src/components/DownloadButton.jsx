import { Download } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";

const BUILD = {
  latest: ["#34D399", "Latest version"],
  building: ["#FBBF24", "A new version is being built, check back in a few minutes"],
  failed: ["#8A93A3", "The newest build didn't finish, so this is the last working version"],
};
const NOTE = "The installer isn't code-signed yet, so Windows may say it protected your PC. Choose More info, then Run anyway.";

// Small footer link; the SmartScreen note only appears after clicking.
export const DownloadLink = () => {
  const { data } = useQuery({ queryKey: ["download-info"], queryFn: async () => (await api.get("/setup/download")).data, staleTime: 120000 });
  if (!data?.show) return null;
  const b = data.url && BUILD[data.build];
  const meta = data.url ? [`FMCC-Setup.exe ${data.version || ""}`.trim(), data.published ? `released ${new Date(data.published).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}` : null, data.size_mb ? `${data.size_mb} MB` : null, "Windows 10/11", b && b[1]].filter(Boolean).join(" · ") : data.message;
  const go = () => toast.info("Your download is starting", { description: NOTE, duration: Infinity, closeButton: true, id: "smartscreen-note" });
  const inner = <><Download size={14} />Download for Windows{b && <i className="dl-dot" style={{ background: b[0] }} data-testid="download-build-status" />}</>;
  return data.url
    ? <a className="tl" href={data.url} title={meta} aria-label={`Download FMCC for Windows. ${meta}`} onClick={go} data-testid="download-exe-button">{inner}</a>
    : <span className="tl" style={{ opacity: 0.55, cursor: "not-allowed" }} title={meta} data-testid="download-exe-button">{inner}</span>;
};
