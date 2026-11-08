import { useState } from "react";
import { Link } from "react-router-dom";
import { PackageOpen, ExternalLink, X } from "lucide-react";
import { useGet } from "@/lib/ui";

export const PackBanner = ({ pack, feature }) => {
  const { data } = useGet("extras", "/extras");
  const [hidden, setHidden] = useState(() => localStorage.getItem(`fmcc-hide-pack-${pack}`) === "1");
  const it = data?.items.find((i) => i.key === pack);
  if (!it || it.found || hidden) return null;
  const hide = () => { localStorage.setItem(`fmcc-hide-pack-${pack}`, "1"); setHidden(true); };
  return (
    <div className="banner" style={{ marginBottom: 16, alignItems: "center", flexWrap: "wrap" }} data-testid={`pack-banner-${pack}`}>
      <PackageOpen size={16} style={{ flexShrink: 0 }} />
      <span style={{ flex: "1 1 280px" }}>{feature} needs <b>{it.name}</b>, which isn't installed yet.{it.download ? ` It's in your Downloads (${it.download.file}), ready to install.` : ""}</span>
      <a className="btn" href={it.page} target="_blank" rel="noreferrer" data-testid={`pack-banner-get-${pack}`}><ExternalLink size={13} />Get it</a>
      <Link className="btn btn-p" to="/extras" data-testid={`pack-banner-open-${pack}`}>{it.download ? "Install it" : "Downloads you need"}</Link>
      <button className="ib" title="Hide this reminder" onClick={hide} data-testid={`pack-banner-hide-${pack}`}><X size={13} /></button>
    </div>
  );
};
