import { Download } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export const DownloadButton = ({ compact }) => {
  const { data } = useQuery({ queryKey: ["download-info"], queryFn: async () => (await api.get("/setup/download")).data, staleTime: 600000 });
  if (!data?.show) return null;
  const meta = [data.version, data.size_mb ? `${data.size_mb} MB` : null, "Windows 10/11"].filter(Boolean).join(" · ");
  return (
    <div className={`dl-box${compact ? " compact" : ""}`} data-testid="download-box">
      {data.url ? <a className="btn btn-g btn-l" href={data.url} data-testid="download-exe-button"><Download size={18} />Download FMCC for Windows</a>
        : <button className="btn btn-l" disabled data-testid="download-exe-button"><Download size={18} />Download FMCC for Windows</button>}
      <small data-testid="download-meta">{data.url ? `FMCC-Setup.exe · ${meta}` : data.message}</small>
    </div>
  );
};
