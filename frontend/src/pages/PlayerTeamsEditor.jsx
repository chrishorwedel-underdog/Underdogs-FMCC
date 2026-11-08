import { useState } from "react";
import { AlertTriangle, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { useGet, useAct, TabBar, PageHead } from "@/lib/ui";
import { FacesTab } from "@/components/editor/FacesTab";
import { ClubsTab } from "@/components/editor/ClubsTab";
import { LicensingTab } from "@/components/editor/LicensingTab";

const Files = ({ s }) => {
  const act = useAct();
  const f = s.files;
  return (
    <div className="banner" style={{ marginBottom: 20 }} data-testid="editor-files-banner"><AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
      <span style={{ flex: 1 }}>{f ? <>FMCC's graphics folder holds {f.graphics.pictures} picture(s) at <span className="mono">{f.graphics.folder}</span>{f.lnc.renames ? <> · {f.lnc.renames} rename(s) in <span className="mono">{f.lnc.file}</span>{s.lnc_present === false && <b> · missing (a game update may have removed it)</b>}</> : ""}. </> : "Nothing changed yet. "}
        In FM, turn off "Use skin cache" and reload the skin in Preferences, or restart FM, to see new pictures. Renames show after restarting FM.{!s.desktop && " Browser preview: files go to a sandbox folder, not to FM."}</span>
      {f && <button className="btn" onClick={() => act(() => api.post("/editor/rewrite"), "Files written again", ["editor-status"])} data-testid="editor-rewrite"><RefreshCw size={13} />Write again</button>}
    </div>
  );
};

export default function PlayerTeamsEditor() {
  const [tab, setTab] = useState("faces");
  const { data: s } = useGet("editor-status", "/editor/status");
  return (
    <div data-testid="editor-page">
      <PageHead eyebrow="Faces, logos, names and club attributes" title="Player & Teams Editor">
        <TabBar id="editor" value={tab} onChange={setTab} tabs={[["faces", "Player faces"], ["clubs", "Clubs"], ["licensing", "Licensing fix"]]} />
      </PageHead>
      {!s ? <p className="note">Loading…</p> : <><Files s={s} />{tab === "faces" ? <FacesTab s={s} /> : tab === "clubs" ? <ClubsTab /> : <LicensingTab />}</>}
    </div>
  );
}
