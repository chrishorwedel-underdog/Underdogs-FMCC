import { useRef, useState } from "react";
import { Plus, Trash2, ArrowUp, ArrowDown, FlaskConical, Download, Upload, RotateCcw } from "lucide-react";
import { toast } from "sonner";
import { Switch } from "@/components/ui/switch";
import { api, ago } from "@/lib/api";
import { useGet, useAct } from "@/lib/ui";
import { ParamsEditor } from "@/components/rules/ParamsEditor";
import { RuleItem, ImpactSave } from "@/components/rules/RuleItem";

const OPS = [[">=", "at least"], ["<=", "at most"], ["=", "exactly"], ["!=", "not"]];
const TIMING = [["monthly", "every month"], ["season_end", "at season end"], ["after_matches", "after each set of matches"], ["on_demand", "when I ask"]];
const Blank = (p) => <input className="blank mono" {...p} />;

const Condition = ({ c, fields, set, del, i, rid }) => (
  <span className="cond">
    <select className="blank" value={c.field} onChange={(e) => set({ ...c, field: e.target.value })} data-testid={`rule-${rid}-field-${i}`}>
      {Object.entries(fields).map(([k, [l]]) => <option key={k} value={k}>{l}</option>)}
    </select>
    <select className="blank" value={c.op} onChange={(e) => set({ ...c, op: e.target.value })}>{OPS.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
    <Blank style={{ width: 90 }} value={c.value} onChange={(e) => set({ ...c, value: fields[c.field][1] === "number" && e.target.value !== "" && !isNaN(e.target.value) ? Number(e.target.value) : e.target.value })} data-testid={`rule-${rid}-value-${i}`} />
    <button className="x" onClick={del} title="Remove condition"><Trash2 size={12} /></button>
  </span>
);

const WORD = { pa: "potential", ca: "current ability" };
const opWord = (op) => (OPS.find(([k]) => k === op) || [op, op])[1];
const summary = (r, fields) => (r ? `${r.enabled ? "" : "Off · "}${r.conditions.map((c) => `${fields[c.field]?.[0] || c.field} ${opWord(c.op)} ${c.value}`).join(` ${r.join} `)} → ${WORD[r.action.target]} ${r.action.min} to ${r.action.max}, ${(TIMING.find(([k]) => k === r.timing) || [0, r.timing])[1]}` : null);

const RuleCard = ({ r, fields, set, del, move, test, idx, def, changedAt }) => {
  const a = r.action;
  const upd = (p) => set({ ...r, ...p });
  const title = (
    <><input className="blank" style={{ fontWeight: 600, width: 220 }} value={r.name} onChange={(e) => upd({ name: e.target.value })} aria-label="Rule name" data-testid={`rule-name-${idx}`} />
      <Switch checked={r.enabled} onCheckedChange={(v) => upd({ enabled: v })} aria-label="Rule on or off" data-testid={`rule-enabled-${idx}`} />
      <button className="ib" onClick={() => move(-1)} aria-label="Move up" data-testid={`rule-up-${idx}`}><ArrowUp size={14} /></button><button className="ib" onClick={() => move(1)} aria-label="Move down" data-testid={`rule-down-${idx}`}><ArrowDown size={14} /></button>
      <button className="ib" onClick={del} aria-label="Delete rule" data-testid={`rule-delete-${idx}`}><Trash2 size={14} /></button></>
  );
  return (
    <div className={`rulecard${r.enabled ? "" : " off"}`} data-testid={`rule-card-${idx}`}>
    <RuleItem id={`rule-${idx}`} title={title} help="Players who match every condition (or any, with ‘or’) get this change. The first matching rule wins." now={summary(r, fields)} def={summary(def, fields)}
      changedAt={changedAt} differs={!!def && JSON.stringify(def) !== JSON.stringify(r)} canReset={!!def} onReset={() => set(def)}>
      <p className="sentence">If a player's{" "}
        {r.conditions.map((c, i) => (
          <span key={i}>{i > 0 && <select className="blank" value={r.join} onChange={(e) => upd({ join: e.target.value })}><option value="and">and</option><option value="or">or</option></select>}{" "}
            <Condition c={c} i={i} rid={idx} fields={fields} set={(nc) => upd({ conditions: r.conditions.map((x, j) => (j === i ? nc : x)) })} del={() => r.conditions.length > 1 && upd({ conditions: r.conditions.filter((_, j) => j !== i) })} />{" "}</span>
        ))}
        <button className="btn" style={{ height: 26 }} onClick={() => upd({ conditions: [...r.conditions, { field: "age", op: "<=", value: 21 }] })} data-testid={`rule-add-condition-${idx}`}><Plus size={12} />condition</button>
        , change{" "}<select className="blank" value={a.target} onChange={(e) => upd({ action: { ...a, target: e.target.value } })}><option value="pa">potential</option><option value="ca">current ability</option></select>
        {" "}by <Blank style={{ width: 52 }} type="number" value={a.min} onChange={(e) => upd({ action: { ...a, min: Number(e.target.value) } })} data-testid={`rule-min-${idx}`} />
        {" "}to <Blank style={{ width: 52 }} type="number" value={a.max} onChange={(e) => upd({ action: { ...a, max: Number(e.target.value) } })} data-testid={`rule-max-${idx}`} />,
        never above <Blank style={{ width: 58 }} type="number" value={r.max_value} onChange={(e) => upd({ max_value: Number(e.target.value) })} />,
        {" "}<select className="blank" value={r.timing} onChange={(e) => upd({ timing: e.target.value })}>{TIMING.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>.
      </p>
      {test && <div style={{ marginTop: 10 }}><button className="btn" onClick={test} data-testid={`rule-test-${idx}`}><FlaskConical size={13} />Test this rule</button></div>}
    </RuleItem>
    </div>
  );
};

const Toolbar = ({ doc, reset, imp }) => {
  const file = useRef();
  const exp = () => {
    const blob = new Blob([JSON.stringify({ module: doc.module, data: doc.data }, null, 2)], { type: "application/json" });
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = `fmcc-${doc.module}-rules-v${doc.version}.json`; a.click();
  };
  const onFile = async (e) => {
    const f = e.target.files[0]; e.target.value = "";
    if (!f) return;
    try { const j = JSON.parse(await f.text()); imp(j.data || j); } catch { toast.error("That file isn't an FMCC rules file"); }
  };
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
      <span className="st n" style={{ marginLeft: 0 }} data-testid="rules-version">Version {doc.version || "preset"}</span>
      <button className="btn" onClick={reset} data-testid="rules-reset-button"><RotateCcw size={13} />Reset all to default</button>
      <button className="btn" onClick={exp} data-testid="rules-export-button"><Download size={13} />Export</button>
      <button className="btn" onClick={() => file.current.click()} data-testid="rules-import-button"><Upload size={13} />Import</button>
      <input ref={file} type="file" accept=".json" hidden onChange={onFile} data-testid="rules-import-input" />
    </div>
  );
};

export const RulesTab = ({ module, title, extra }) => {
  const { data: doc } = useGet("rules", `/rules/${module}`, { module });
  const act = useAct();
  const [draft, setDraft] = useState(null);
  const [test, setTest] = useState(null);
  if (!doc) return <p className="note">Loading rules…</p>;
  const data = draft?.version === doc.version ? draft.data : doc.data;
  const setData = (d) => setDraft({ version: doc.version, data: d });
  const save = () => act(() => api.put(`/rules/${module}`, { data, expected_version: doc.version, note: "Edited" }), (d) => `Rules saved as version ${d.version}`, ["rules", "plan", "registration", "elite", "breakout", "dp", "rankings", "development", "report"]).then((r) => { if (r) { setDraft(null); } return r; });
  const check = () => api.post(`/rules/${module}/impact`, { data });
  const dirty = JSON.stringify(data) !== JSON.stringify(doc.data);
  const presets = Object.fromEntries((doc.defaults.rules || []).map((r) => [r.id, r]));
  const reset = () => window.confirm("Reset these rules to the default preset? Your current version stays in the history.") && act(() => api.post(`/rules/${module}/reset`, { expected_version: doc.version }), "Rules reset to the default preset", null);
  const imp = (d) => act(() => api.post(`/rules/${module}/import`, { data: d, expected_version: doc.version, note: "Imported preset" }), "Rules imported", null);
  const runTest = async (r) => { const res = await act(() => api.post(`/rules/${module}/test`, { rule: r }), null, []); if (res) setTest({ name: r.name, ...res }); };
  const rules = data.rules || [];
  const setRule = (i, r) => setData({ ...data, rules: rules.map((x, j) => (j === i ? r : x)) });
  const move = (i, d) => { const j = i + d; if (j < 0 || j >= rules.length) return; const n = [...rules]; [n[i], n[j]] = [n[j], n[i]]; setData({ ...data, rules: n }); };
  return (
    <div className="homegrid" data-testid={`rules-tab-${module}`}>
      <div>
        <div style={{ display: "flex", alignItems: "center", marginBottom: 14, gap: 12, flexWrap: "wrap" }}><div className="ttl">{title}</div><span style={{ marginLeft: "auto" }} /><Toolbar doc={doc} reset={reset} imp={imp} /></div>
        {extra && extra(data, setData)}
        {doc.kind === "params" ? <ParamsEditor module={module} doc={doc} params={data.params} set={(p) => setData({ ...data, params: p })} /> : (
          <div style={{ display: "grid", gap: 14 }}>
            {rules.map((r, i) => <RuleCard key={r.id} idx={i} r={r} fields={doc.fields} def={presets[r.id]} changedAt={doc.changed_at?.[r.id]} set={(nr) => setRule(i, nr)} del={() => setData({ ...data, rules: rules.filter((_, j) => j !== i) })}
              move={(d) => move(i, d)} test={() => runTest(r)} />)}
            <button className="btn" style={{ justifySelf: "start" }} data-testid="rule-add-button"
              onClick={() => setData({ ...data, rules: [...rules, { id: `r-${Date.now()}`, name: "New rule", enabled: true, join: "and", timing: "season_end", max_value: 200, conditions: [{ field: "age", op: "<=", value: 21 }], action: { target: "pa", min: 1, max: 3 } }] })}><Plus size={13} />Add rule</button>
          </div>
        )}
      </div>
      <div style={{ display: "grid", gap: 16, alignContent: "start" }}>
        <ImpactSave dirty={dirty} draftKey={JSON.stringify(data)} check={check} save={save} summary="You have unsaved changes. Check who they affect, then save." />
        {test && <div className="card" data-testid="rule-test-result"><div className="ttl">Test: {test.name}</div>
          <p className="sent"><b>{test.count}</b> of {test.population} players would qualify right now. Nothing is applied.</p>
          <p className="note" style={{ marginTop: 8 }}>{test.names.join(", ") || "Nobody yet."}</p></div>}
        <div className="card" data-testid="rules-history"><div className="ttl">Rule history</div>
          <p className="note" style={{ marginTop: 4 }}>Every saved change is kept. Changes only affect future runs.</p>
          {doc.history.length === 0 && <p className="note" style={{ marginTop: 10 }}>Using the default preset.</p>}
          {doc.history.map((h) => <div className="row" key={h.version}><span className="mono">v{h.version}</span><div style={{ flex: 1 }}>{h.note}<small>{ago(h.created_at)}</small></div></div>)}
        </div>
      </div>
    </div>
  );
};
