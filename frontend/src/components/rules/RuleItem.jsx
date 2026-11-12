import { useState } from "react";
import { RotateCcw, Save, Users } from "lucide-react";
import { ago } from "@/lib/api";
import { useAct } from "@/lib/ui";

export const RuleItem = ({ id, title, help, now, def, changedAt, differs, onReset, canReset = true, children, off }) => (
  <div className={`card rule-item${off ? " off" : ""}`} data-testid={`rule-item-${id}`}>
    <div className="ttl" style={{ gap: 8, flexWrap: "wrap" }}>{title}
      {differs && <span className="st a" data-testid={`rule-item-changed-${id}`}>Changed from default</span>}
      <span style={{ marginLeft: "auto" }} />
      {canReset && <button className="btn" style={{ height: 28 }} disabled={!differs} onClick={onReset} title="Put just this rule back to its default" data-testid={`rule-item-reset-${id}`}><RotateCcw size={12} />Reset this rule</button>}
    </div>
    {help && <p className="note" style={{ margin: "4px 0 10px" }}>{help}</p>}
    {children}
    <div className="rule-meta">
      <span data-testid={`rule-item-now-${id}`}>Now: <b>{now}</b></span>
      <span data-testid={`rule-item-default-${id}`}>Default: <b>{def ?? "None (your own rule)"}</b></span>
      <span data-testid={`rule-item-changed-at-${id}`}>Last changed: <b>{changedAt ? ago(changedAt) : "never"}</b></span>
    </div>
  </div>
);

export const ImpactSave = ({ dirty, draftKey, check, save, summary, children }) => {
  const act = useAct();
  const [res, setRes] = useState(null);
  const shown = res?.key === draftKey ? res : null;
  const preview = () => act(check, null, []).then((r) => r && setRes({ ...r, key: draftKey }));
  const confirm = () => save().then((r) => r && setRes(null));
  return (
    <div className="card" data-testid="rules-save-card">
      <div className="ttl">Save changes</div>
      <p className="note" data-testid="rules-save-summary">{dirty ? summary || "You have unsaved changes." : "No unsaved changes."}</p>
      {!shown && <button className="btn btn-p" style={{ marginTop: 8 }} disabled={!dirty} onClick={preview} data-testid="rules-preview-button"><Users size={13} />Check who it affects</button>}
      {shown && <div className="impact" data-testid="rules-impact">
        <b data-testid="rules-impact-count">{shown.affected} of {shown.population} players affected</b>
        <small style={{ display: "block", color: "var(--mut)", marginTop: 3 }}>{shown.note}</small>
        <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
          <button className="btn btn-p" onClick={confirm} data-testid="rules-save-button"><Save size={13} />Save</button>
          <button className="btn" onClick={() => setRes(null)} data-testid="rules-impact-cancel">Keep editing</button>
        </div>
      </div>}
      {children}
    </div>
  );
};
