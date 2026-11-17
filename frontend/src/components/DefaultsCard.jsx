import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { loadAppearance } from "@/lib/appearance";

// Settings: save what this career has set up as the default for every new career.
export const DefaultsCard = () => {
  const { data } = useGet("defaults", "/defaults");
  const act = useAct();
  if (!data) return null;
  const save = (k) => act(() => api.post(`/defaults/${k}/save`, k === "appearance" ? { appearance: loadAppearance() } : {}), "Saved as the default for new games", ["defaults"]);
  const clear = (k) => act(() => api.delete(`/defaults/${k}`), "Default cleared", ["defaults"]);
  return (
    <div className="card rise d3" data-testid="defaults-card">
      <div className="ttl">Defaults for new games</div>
      <p className="note" style={{ marginTop: 6 }}>Copy what you've set up in this career into every career you start from now on. Existing careers never change.</p>
      {data.areas.map((a) => (
        <div className="row" key={a.key} data-testid={`default-row-${a.key}`}>
          <div style={{ flex: 1 }}>{a.label}<small data-testid={`default-status-${a.key}`}>{a.saved ? "Saved as a default" : "No default saved"}</small></div>
          <button className="btn" onClick={() => save(a.key)} data-testid={`default-save-${a.key}`}>Save as default</button>
          {a.saved && <button className="btn" onClick={() => clear(a.key)} data-testid={`default-clear-${a.key}`}>Clear default</button>}
        </div>
      ))}
    </div>
  );
};

// Setup: every saved default with a switch, all on. Switch one off for this career only.
export const DefaultsPick = ({ value, onChange }) => {
  const { data } = useGet("defaults", "/defaults");
  const saved = (data?.areas || []).filter((a) => a.saved);
  if (!saved.length) return null;
  const on = (k) => value === undefined || value.includes(k);
  const toggle = (k, v) => onChange((value === undefined ? saved.map((a) => a.key) : value).filter((x) => x !== k).concat(v ? [k] : []));
  return (
    <div className="card" style={{ marginTop: 18, textAlign: "left" }} data-testid="setup-defaults">
      <div className="ttl">Your defaults</div>
      <p className="note" style={{ marginTop: 6 }}>Penalties and Seed a Surname apply after the first save read; the rest apply straight away.</p>
      {saved.map((a) => (
        <div className="row" key={a.key}>
          <div style={{ flex: 1 }}>{a.label}</div>
          <Switch checked={on(a.key)} onCheckedChange={(v) => toggle(a.key, v)} data-testid={`setup-default-${a.key}`} />
        </div>
      ))}
    </div>
  );
};
