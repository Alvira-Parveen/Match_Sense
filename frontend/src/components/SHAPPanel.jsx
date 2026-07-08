import React from "react";

// Pretty labels for the six XGB features returned by /api/predict
const NICE = {
    elo_diff: "ELO Rating Δ",
    form_diff: "Recent Form Δ",
    h2h_ratio: "Head-to-Head",
    attack_diff: "Attack Strength Δ",
    defense_diff: "Defense Strength Δ",
    injury_delta: "Injury Delta",
};

export default function SHAPPanel({ features, shap }) {
    // Prefer real Shapley values from the SHAP TreeExplainer; fall back to the
    // ensemble-weighted "impact" list when SHAP isn't available.
    const useReal = Array.isArray(shap) && shap.length > 0;
    const rows = useReal
        ? shap
              .map((s) => ({
                  name: NICE[s.name] || s.name,
                  impact: s.shap_home,
                  value: s.value,
              }))
              .sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact))
        : (features || []).map((f) => ({ name: f.name, impact: f.impact, value: f.value }));

    if (!rows.length) return null;
    const maxAbs = Math.max(...rows.map((f) => Math.abs(f.impact))) || 1;

    return (
        <div data-testid="shap-panel" className="rounded-sm border border-hairline bg-cream-card p-5">
            <div className="mb-1 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.25em] text-mutedink">
                <span>{useReal ? "SHAP TreeExplainer" : "SHAP-style attribution"}</span>
                {useReal && <span className="rounded-full bg-coral/10 px-2 py-0.5 text-[9px] text-coral">shap.TreeExplainer</span>}
            </div>
            <h3 className="mb-4 font-display text-xl font-bold tracking-tight">
                Why the model favours this side
            </h3>
            <div className="space-y-3">
                {rows.map((f) => {
                    const pct = (Math.abs(f.impact) / maxAbs) * 100;
                    const positive = f.impact >= 0;
                    return (
                        <div key={f.name} data-testid={`shap-feature-${f.name.replace(/\s+/g, "-").toLowerCase()}`}>
                            <div className="mb-1 flex items-baseline justify-between">
                                <span className="font-mono text-xs uppercase tracking-[0.15em] text-bodytext">{f.name}</span>
                                <span className={`font-mono text-xs font-bold tabular-nums ${positive ? "text-volt" : "text-signal"}`}>
                                    {positive ? "+" : ""}{f.impact.toFixed(2)}{useReal ? "" : " pts"}
                                </span>
                            </div>
                            <div className="grid grid-cols-2 gap-0 overflow-hidden rounded-sm bg-cream-strong">
                                <div className="flex justify-end">
                                    {!positive && <div className="h-3 bg-signal transition-all" style={{ width: `${pct}%` }} />}
                                </div>
                                <div className="flex justify-start">
                                    {positive && <div className="h-3 bg-volt transition-all" style={{ width: `${pct}%` }} />}
                                </div>
                            </div>
                            <div className="mt-1 font-mono text-[10px] text-mutedink">
                                {typeof f.value === "number" ? f.value.toFixed(2) : String(f.value)}
                            </div>
                        </div>
                    );
                })}
            </div>
            <div className="mt-5 flex items-center gap-4 border-t border-hairline/60 pt-3 font-mono text-[10px] uppercase tracking-[0.15em] text-mutedink">
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 bg-volt" /> Favors home</span>
                <span className="flex items-center gap-1.5"><span className="h-2 w-2 bg-signal" /> Favors away</span>
            </div>
        </div>
    );
}
