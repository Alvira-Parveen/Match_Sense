import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, flagEmoji } from "../lib/api";
import { ArrowLeft, CheckCircle, CircleDashed } from "@phosphor-icons/react";

const FLAG = {
    ARG: "AR", FRA: "FR", BRA: "BR", ESP: "ES", ENG: "GB", POR: "PT",
    BEL: "BE", COL: "CO", NOR: "NO", USA: "US", MAR: "MA", MEX: "MX",
    SUI: "CH", PAR: "PY", EGY: "EG", CAN: "CA",
};

const ROUND_TITLES = { R16: "Round of 16", QF: "Quarter-finals", SF: "Semi-finals", F: "Final", "3P": "Third-place Playoff" };

export default function ResultsArchivePage() {
    const [bracket, setBracket] = useState(null);
    const [err, setErr] = useState("");

    useEffect(() => {
        api.get("/bracket").then((r) => setBracket(r.data)).catch(() => setErr("Failed to load bracket"));
    }, []);

    if (err) return <div className="mx-auto max-w-3xl px-6 py-20 text-signal">{err}</div>;
    if (!bracket) return <div className="mx-auto max-w-3xl px-6 py-20 text-mutedink">Loading archive…</div>;

    const rounds = ["R16", "QF", "SF", "3P", "F"];
    const byRound = rounds.map((r) => (bracket.matches || []).filter((m) => m.round === r));
    const frozenCount = (bracket.actual_results && Object.keys(bracket.actual_results).length) || 0;
    const totalMatches = (bracket.matches || []).length;

    return (
        <div data-testid="archive-page" className="mx-auto max-w-[1100px] px-6 py-10 sm:px-10">
            <Link to="/" className="focus-ring inline-flex items-center gap-2 rounded-md border border-hairline bg-canvas px-3 py-1.5 text-xs text-ink hover:border-coral">
                <ArrowLeft size={12} weight="bold" /> Dashboard
            </Link>

            <div className="mt-8">
                <div className="text-[11px] uppercase tracking-widest text-mutedink">Public archive · read only</div>
                <h1 className="mt-2 font-display text-5xl tracking-tight text-ink">Results Archive</h1>
                <p className="mt-3 max-w-2xl text-base text-mutedink">
                    Which parts of the bracket are officially locked-in versus still projected by the model. Coral rows are actual FIFA results; muted rows are model forecasts.
                </p>

                <div className="mt-8 grid gap-3 sm:grid-cols-2">
                    <div className="rounded-md border border-coral/40 bg-coral/[0.05] p-5">
                        <div className="text-[10px] uppercase tracking-widest text-coral">Officially played</div>
                        <div className="mt-1 font-display text-4xl tabular-nums text-ink" data-testid="archive-frozen-count">{frozenCount} <span className="text-2xl text-mutedink">/ {totalMatches}</span></div>
                    </div>
                    <div className="rounded-md border border-hairline bg-cream-card p-5">
                        <div className="text-[10px] uppercase tracking-widest text-mutedink">Projected champion (current model)</div>
                        <div className="mt-1 font-display text-4xl tracking-tight text-ink">{bracket.predicted_champion || "—"}</div>
                    </div>
                </div>
            </div>

            <div className="mt-10 space-y-10">
                {rounds.map((r, i) => (
                    <div key={r}>
                        <div className="mb-4 text-[11px] uppercase tracking-widest text-mutedink">{ROUND_TITLES[r]}</div>
                        <div className="space-y-2">
                            {byRound[i].map((m) => (
                                <Row key={m.id} match={m} />
                            ))}
                            {byRound[i].length === 0 && <div className="text-sm text-mutedink">No matches yet.</div>}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

function Row({ match }) {
    const p = match.prediction || {};
    const winner = match.predicted_winner;
    const homeWon = winner === match.home;
    const isActual = match.is_actual;
    return (
        <div
            data-testid={`archive-row-${match.id}`}
            className={`flex flex-wrap items-center gap-4 rounded-md border p-4 ${isActual ? "border-coral/40 bg-coral/[0.04]" : "border-hairline bg-cream-card"}`}
        >
            <div className="w-16 font-mono text-[10px] uppercase tracking-widest text-mutedink">{match.id}</div>
            <TeamCell code={match.home} won={homeWon} winnerAvailable={!!winner} />
            <span className="text-xs text-mutedink">vs</span>
            <TeamCell code={match.away} won={!homeWon} winnerAvailable={!!winner} />
            <div className="flex-1" />
            {isActual ? (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-coral/40 bg-coral/10 px-3 py-1 text-[10px] uppercase tracking-widest text-coral">
                    <CheckCircle size={12} weight="fill" /> Actual · {winner}
                </span>
            ) : (
                <span className="inline-flex items-center gap-1.5 rounded-full border border-hairline bg-canvas px-3 py-1 text-[10px] uppercase tracking-widest text-mutedink">
                    <CircleDashed size={12} weight="regular" /> Projected · {winner} @ {(Math.max(p.prob_home || 0, p.prob_away || 0) * 100).toFixed(0)}%
                </span>
            )}
        </div>
    );
}

function TeamCell({ code, won, winnerAvailable }) {
    return (
        <div className="flex items-center gap-2">
            <span className="text-xl">{flagEmoji(FLAG[code])}</span>
            <span className={`font-display text-lg tracking-tight ${winnerAvailable && won ? "text-ink" : "text-mutedink"}`}>{code || "TBD"}</span>
        </div>
    );
}