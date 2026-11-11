import { Download } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

const BUILD = {
  latest: ["#34D399", "Latest version"],
  building: ["#FBBF24", "A new version is being built, check back in a few minutes"],
  failed: ["#8A93A3", "The newest build didn't finish, so this is the last working version"],
};

export const DownloadButton = ({ compact }) => {
  const { data } = useQuery({ queryKey: ["download-info"], queryFn: async () => (await api.get("/setup/download")).data, staleTime: 120000 });
  if (!data?.show) return null;
  const b = data.url && BUILD[data.build];
  const meta = [data.version, data.published ? `released ${new Date(data.published).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}` : null, data.size_mb ? `${data.size_mb} MB` : null, "Windows 10/11"].filter(Boolean).join(" · ");
  return (
    <div className={`dl-box${compact ? " compact" : ""}`} data-testid="download-box">
      {data.url ? <a className="btn btn-g btn-l" href={data.url} data-testid="download-exe-button"><Download size={18} />Download FMCC for Windows</a>
        : <button className="btn btn-l" disabled data-testid="download-exe-button"><Download size={18} />Download FMCC for Windows</button>}
      <small data-testid="download-meta">{data.url ? `FMCC-Setup.exe · ${meta}` : data.message}</small>
      {b && <small style={{ display: "inline-flex", alignItems: "center", gap: 6 }} data-testid="download-build-status"><i style={{ width: 7, height: 7, borderRadius: "50%", background: b[0], display: "inline-block" }} />{b[1]}</small>}
      {data.url && <small className="note" style={{ opacity: 0.75 }} data-testid="download-smartscreen-note">The installer isn't code-signed yet, so Windows may say it protected your PC. Choose More info, then Run anyway.</small>}
    </div>
  );
};
