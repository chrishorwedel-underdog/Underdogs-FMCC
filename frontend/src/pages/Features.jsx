import { useNavigate } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import { useAct, PageHead } from "@/lib/ui";
import { Switch } from "@/components/ui/switch";
import { NAV } from "@/constants/nav";
import { FEATURE_TEXT, useFeatures } from "@/lib/features";

const ALL = [...NAV, { to: "/dof", key: "dof", label: "Chat with your Director of Football", c: "#E5302F", Icon: Sparkles }];

const FeatureCard = ({ f, on, set }) => {
  const [about, example] = FEATURE_TEXT[f.key];
  const home = f.key === "home";
  return (
    <div className={`card feat-card${on ? "" : " off"}`} style={{ "--c": f.c }} data-testid={`feature-card-${f.key}`}>
      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <span className="tile2"><f.Icon size={20} strokeWidth={2.2} /></span>
        <b style={{ flex: 1 }}>{f.label}</b>
        {home ? <span className="st n">Always on</span> : <Switch checked={on} onCheckedChange={set} data-testid={`feature-switch-${f.key}`} />}
      </div>
      <p className="note" style={{ margin: "10px 0 6px" }}>{about}</p>
      <small className="note" style={{ opacity: 0.8 }}><b>For example:</b> {example}</small>
    </div>
  );
};

export default function Features() {
  const { data } = useFeatures();
  const act = useAct();
  const nav = useNavigate();
  if (!data) return null;
  const save = (features) => act(() => api.put("/features", { features }), null, ["features", "notices", "countdowns", "home"]);
  const all = (v) => save(Object.fromEntries(Object.keys(data.features).map((k) => [k, v])));
  const done = () => act(() => api.post("/features/seen"), null, ["features"]).then(() => nav("/"));
  return (
    <div data-testid="features-page">
      <PageHead eyebrow="Your career, your way" title="Choose your features">
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button className="btn" onClick={() => all(true)} data-testid="features-all-on">Turn all on</button>
          <button className="btn" onClick={() => all(false)} data-testid="features-all-off">Turn all off</button>
          <button className="btn btn-g" onClick={done} data-testid="features-done">Done</button>
        </div>
      </PageHead>
      <p className="note" style={{ marginBottom: 18 }}>Pick what FMCC does in this career. You can change this any time from Features at the bottom of the app. Turning a feature off never deletes anything; it just stops its automatic work and locks it in the menu.</p>
      <div className="feat-grid">{ALL.map((f) => <FeatureCard key={f.key} f={f} on={f.key === "home" || data.features[f.key] !== false} set={(v) => save({ [f.key]: v })} />)}</div>
    </div>
  );
}
