import { useState } from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { api, errMsg } from "@/lib/api";

const PRESETS = ["Boss", "Gaffer", "Coach", "Mister", "Manager", "Chief"];

export const AddressPick = ({ value, onChange }) => {
  const custom = !PRESETS.includes(value);
  return (
    <div style={{ marginTop: 16 }} data-testid="address-pick">
      <label className="lbl">What the game calls you</label>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" }}>
        {PRESETS.map((p) => <button key={p} type="button" className={`btn${value === p ? " btn-p" : ""}`} onClick={() => onChange(p)} data-testid={`address-${p.toLowerCase()}`}>{p}</button>)}
        <input className="inp" style={{ width: 200 }} placeholder="Or type your own, e.g. your name" maxLength={30} value={custom ? value : ""} onChange={(e) => onChange(e.target.value)} data-testid="address-custom" />
      </div>
      <small style={{ color: "var(--dim)" }}>FMCC greets you this way, for example "Good morning, {value?.trim() || "Boss"}."</small>
    </div>
  );
};

export const AddressCard = ({ current }) => {
  const [v, setV] = useState(current || "Boss");
  const qc = useQueryClient();
  const save = async () => {
    try {
      await api.put("/settings/address", { address: v.trim() });
      qc.invalidateQueries({ queryKey: ["state"] });
      qc.invalidateQueries({ queryKey: ["home"] });
      toast.success(`FMCC will call you ${v.trim()}`);
    } catch (e) { toast.error(errMsg(e)); }
  };
  return (
    <div className="card rise d4" data-testid="address-card">
      <div className="ttl">What the game calls you</div>
      <AddressPick value={v} onChange={setV} />
      <button className="btn btn-p" style={{ marginTop: 10 }} disabled={!v.trim() || v.trim() === current} onClick={save} data-testid="address-save">Save</button>
    </div>
  );
};
