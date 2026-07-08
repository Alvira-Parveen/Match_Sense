import React, { useEffect, useState } from "react";
import { api, flagEmoji } from "../lib/api";
import { CheckCircle, XCircle, Trophy } from "@phosphor-icons/react";

const FLAG = {
    Spain:"ES",Netherlands:"NL",Germany:"DE",Argentina:"AR",France:"FR",Croatia:"HR",
    Brazil:"BR",Portugal:"PT",Uruguay:"UY",Belgium:"BE",England:"GB",Colombia:"CO",
    Chile:"CL",Mexico:"MX",Algeria:"DZ",Nigeria:"NG",Switzerland:"CH",Russia:"RU",
    Denmark:"DK",Sweden:"SE",Japan:"JP",USA:"US","Costa Rica":"CR",Ghana:"GH",
    Greece:"GR","South Korea":"KR",Morocco:"MA",Italy:"IT",Czechia:"CZ",Wales:"GB-WLS",
    Iran:"IR",Ecuador:"EC",Senegal:"SN",Cameroon:"CM",Serbia:"RS",Canada:"CA",
    Poland:"PL","Saudi Arabia":"SA",Australia:"AU",
};

export default function ModelReportCard() {
    const [data, setData] = useState(null);
    useEffect(() => {
        api.get("/replay").then((r) => {
            const d = r.data;
            const CURRENT_16 = new Set([
                "Argentina","France","Brazil","Spain","England","Portugal",
                "Belgium","Colombia","Norway","USA","Morocco","Mexico",
                "Switzerland","Paraguay","Egypt","Canada",
            ]);
            const inCurrent = (x) => CURRENT_16.has(x.home) && CURRENT_16.has(x.away);
            setData({
                ...d,
                best_calls: (d.best_calls || []).filter(inCurrent).slice(0, 5),
                worst_calls: (d.worst_calls || []).filter(inCurrent).slice(0, 5),
                all_calls: (d.all_calls || []).filter(inCurrent),
            });
        }).catch(() => {});
    }, []);
    if (!data) return null;

    return (
        <section
            data-testid="report-card-section"
            id="report"
            className="border-b border-hairline py-16"
        >
            <div className="mx-auto max-w-[1400px] px-6 sm:px-10">
                <div className="mb-8">
                    <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-mutedink">
                        Model Explainability · Historical Replay
                    </div>
                    <h2 className="mt-2 font-display text-3xl font-medium tracking-tight sm:text-4xl">
                        Model Report Card
                    </h2>
                </div>
                <div className="grid gap-4 sm:grid-cols-3">
                    <Metric label="Accuracy" value={`${(data.accuracy*100).toFixed(1)}%`} tone="volt" />
                    <Metric label="Avg Brier" value={data.avg_brier.toFixed(3)} tone="electric" />
                    <Metric label="Matches Replayed" value={data.n_matches} tone="slate" />
                </div>
                <div className="mt-8 grid gap-6 lg:grid-cols-2">
                    <Column title="Best Calls" icon={<Trophy weight="fill" className="text-electric" size={16} />} rows={data.best_calls} good />
                    <Column title="Worst Calls" icon={<XCircle weight="fill" className="text-signal" size={16} />} rows={data.worst_calls} />
                </div>
            </div>
        </section>
    );
}

function Metric({ label, value, tone }) {
    const t = tone === "volt" ? "text-volt" : tone === "electric" ? "text-electric" : "text-ink";
    return (
        <div className="rounded-sm border border-hairline bg-cream-card p-6">
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-mutedink">{label}</div>
            <div className={`mt-2 font-display text-5xl font-medium tabular-nums ${t}`}>{value}</div>
        </div>
    );
}

function Column({ title, icon, rows, good }) {
    return (
        <div>
            <div className="mb-3 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.2em] text-mutedink">
                {icon} {title}
            </div>
            <div className="space-y-2">
                {rows.map((r, i) => {
                    const pct = Math.max(r.prob_home, r.prob_draw, r.prob_away) * 100;
                    return (
                        <div key={i} data-testid={`replay-${good?"best":"worst"}-${i}`} className={`flex items-center justify-between rounded-sm border p-3 ${r.hit ? "border-volt/30 bg-volt/[0.04]" : "border-signal/30 bg-signal/[0.04]"}`}>
                            <div className="flex items-center gap-3">
                                <span>{flagEmoji(FLAG[r.home])}</span>
                                <span className="font-display text-sm font-bold tracking-tight">{r.home} vs {r.away}</span>
                                <span>{flagEmoji(FLAG[r.away])}</span>
                            </div>
                            <div className="flex items-center gap-3 font-mono text-[10px] uppercase tracking-[0.15em]">
                                <span className="text-mutedink">
                                    predicted {
                                        r.predicted === "home_win" ? `${r.home} win` :
                                        r.predicted === "away_win" ? `${r.away} win` :
                                        r.predicted
                                    } @ {pct.toFixed(0)}%
                                </span>
                                {r.hit ? <CheckCircle weight="fill" size={16} className="text-volt" /> : <XCircle weight="fill" size={16} className="text-signal" />}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
