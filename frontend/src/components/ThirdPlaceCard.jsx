import React from "react";
import { flagEmoji } from "../lib/api";
import { Medal } from "@phosphor-icons/react";

const FLAG = {
    ARG: "AR", FRA: "FR", BRA: "BR", ESP: "ES", ENG: "GB", POR: "PT",
    BEL: "BE", COL: "CO", NOR: "NO", USA: "US", MAR: "MA", MEX: "MX",
    SUI: "CH", PAR: "PY", EGY: "EG", CAN: "CA",
};

export default function ThirdPlaceCard({ bracket, onSelect }) {
    if (!bracket) return null;
    const tp = (bracket.matches || []).find((m) => m.round === "3P");
    if (!tp) return null;
    const p = tp.prediction || {};
    const homeFav = (p.prob_home || 0) >= (p.prob_away || 0);

    return (
        <section
            data-testid="third-place-section"
            aria-labelledby="tp-title"
            className="border-b border-hairline py-16"
        >
            <div className="mx-auto max-w-[1200px] px-6 sm:px-10">
                <div className="mb-6 flex items-baseline gap-3">
                    <Medal size={18} weight="fill" className="text-amber" />
                    <div className="text-[11px] uppercase tracking-widest text-mutedink">
                        Bonus match · 19 July 2026 · Hard Rock Stadium, Miami
                    </div>
                </div>
                <h2 id="tp-title" className="font-display text-4xl tracking-tight text-ink sm:text-5xl">
                    Third-Place Playoff
                </h2>
                <p className="mt-3 max-w-2xl text-sm text-mutedink">
                    The two Semi-final losers meet the day before the Final. Contested by the model&apos;s projected 3rd &amp; 4th-place teams.
                </p>

                <button
                    data-testid="third-place-card"
                    onClick={() => onSelect && onSelect(tp)}
                    className="focus-ring mt-8 grid w-full grid-cols-1 items-center gap-8 rounded-xl border border-hairline bg-cream-card p-8 text-left transition-colors hover:border-coral sm:grid-cols-3"
                >
                    <TeamBlock code={tp.home} pct={p.prob_home} xg={p.xg_home} fav={homeFav} align="left" />
                    <div className="text-center">
                        <div className="font-display text-4xl tracking-tight text-mutedink">VS</div>
                        {p.prob_draw !== undefined && (
                            <div className="mt-2 text-[11px] uppercase tracking-widest text-mutedink">
                                Draw {(p.prob_draw * 100).toFixed(0)}%
                            </div>
                        )}
                    </div>
                    <TeamBlock code={tp.away} pct={p.prob_away} xg={p.xg_away} fav={!homeFav} align="right" />
                </button>

                {tp.predicted_winner && (
                    <div className="mt-6 inline-flex items-center gap-2 rounded-full border border-amber/40 bg-amber/10 px-4 py-2">
                        <Medal size={14} weight="fill" className="text-amber" />
                        <span className="text-[11px] uppercase tracking-widest text-mutedink">
                            Projected bronze medal
                        </span>
                        <span className="font-display text-lg text-ink">{tp.predicted_winner}</span>
                    </div>
                )}
            </div>
        </section>
    );
}

function TeamBlock({ code, pct, xg, fav, align }) {
    return (
        <div className={align === "right" ? "sm:text-right" : "sm:text-left"}>
            <div className={`flex items-center gap-3 ${align === "right" ? "sm:justify-end" : ""}`}>
                <span className="text-3xl leading-none">{flagEmoji(FLAG[code])}</span>
                <div>
                    <div className={`font-display text-2xl tracking-tight ${fav ? "text-ink" : "text-mutedink"}`}>{code || "TBD"}</div>
                    <div className="text-[10px] uppercase tracking-widest text-mutedink">Win probability</div>
                </div>
            </div>
            <div className={`mt-2 flex items-baseline gap-2 ${align === "right" ? "sm:justify-end" : ""}`}>
                <span className={`font-display text-4xl tabular-nums ${fav ? "text-coral" : "text-mutedink"}`}>
                    {pct !== undefined ? (pct * 100).toFixed(0) : "—"}<span className="text-xl">%</span>
                </span>
                {xg !== undefined && <span className="font-mono text-xs text-mutedink">xG {xg.toFixed(2)}</span>}
            </div>
        </div>
    );
}
