import React from "react";
import { flagEmoji } from "../lib/api";
import { CaretRight } from "@phosphor-icons/react";

const ROUND_TITLES = {
    R16: "Round of 16",
    QF: "Quarter-finals",
    SF: "Semi-finals",
    F: "Final",
};

export default function Bracket({ bracket, onSelectMatch, favoriteTeam }) {
    if (!bracket) return null;
    const rounds = ["R16", "QF", "SF", "F"];
    const byRound = rounds.map((r) =>
        bracket.matches.filter((m) => m.round === r),
    );

    return (
        <section
            data-testid="bracket-section"
            id="bracket"
            aria-labelledby="bracket-title"
            className="border-b border-hairline py-16"
        >
            <div className="mx-auto max-w-[1400px] px-6 sm:px-10">
                <div className="mb-10 flex items-end justify-between">
                    <div>
                        <div className="text-[11px] uppercase tracking-widest text-mutedink">
                            Projected · Model Simulation · Pre-Tournament
                        </div>
                        <h2
                            id="bracket-title"
                            className="mt-2 font-display text-4xl font-medium tracking-tight text-ink sm:text-5xl"
                        >
                            The Knockout Bracket
                        </h2>
                        <p className="mt-3 max-w-2xl text-sm text-mutedink">
                            All fixtures below are the model&apos;s current forecast — the FIFA World Cup 2026 knockouts begin 29 June. No team has been eliminated yet.
                        </p>
                    </div>
                    <div className="hidden font-mono text-[10px] uppercase tracking-[0.2em] text-mutedink sm:block">
                        Predicted champion:{" "}
                        <span className="text-electric">
                            {bracket.predicted_champion}
                        </span>
                    </div>
                </div>

                <div
                    className="term-scroll overflow-x-auto"
                    role="region"
                    aria-label="World Cup bracket"
                >
                    <div className="flex min-w-[1200px] items-stretch gap-4">
                        {byRound.map((matches, idx) => (
                            <div
                                key={rounds[idx]}
                                data-testid={`bracket-round-${rounds[idx].toLowerCase()}`}
                                className="flex flex-1 flex-col"
                            >
                                <div className="mb-4 font-mono text-[10px] uppercase tracking-[0.25em] text-mutedink">
                                    {ROUND_TITLES[rounds[idx]]}
                                </div>
                                <div
                                    className={`flex flex-1 flex-col justify-around gap-4`}
                                >
                                    {matches.map((m) => (
                                        <BracketMatch
                                            key={m.id}
                                            match={m}
                                            onClick={() => onSelectMatch(m)}
                                            favoriteTeam={favoriteTeam}
                                        />
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}

function BracketMatch({ match, onClick, favoriteTeam }) {
    const p = match.prediction || {};
    const homeFav = p.prob_home >= p.prob_away;
    const winner = match.predicted_winner;
    const highlightFav =
        favoriteTeam &&
        (match.home === favoriteTeam || match.away === favoriteTeam);

    return (
        <button
            data-testid={`bracket-match-${match.id}`}
            onClick={onClick}
            className={`focus-ring group flex flex-col rounded-sm border bg-cream-card p-3 text-left transition-all hover:-translate-y-0.5 hover:border-ink/30 ${
                highlightFav
                    ? "border-electric/60 shadow-[0_0_0_1px_rgba(225,255,0,0.2)]"
                    : "border-hairline"
            }`}
            aria-label={`Open ${match.home} vs ${match.away} match brief`}
        >
            <div className="mb-2 flex items-center justify-between">
                <div className="font-mono text-[9px] uppercase tracking-[0.2em] text-mutedink">
                    {match.id}
                </div>
                <CaretRight
                    size={12}
                    className="text-mutedink transition-colors group-hover:text-volt"
                />
            </div>

            <TeamRow
                code={match.home}
                pct={p.prob_home}
                xg={p.xg_home}
                isWinner={winner === match.home}
                color="volt"
            />
            <TeamRow
                code={match.away}
                pct={p.prob_away}
                xg={p.xg_away}
                isWinner={winner === match.away}
                color="signal"
            />

            {p.prob_draw !== undefined && (
                <div className="mt-1.5 font-mono text-[9px] uppercase tracking-[0.15em] text-mutedink">
                    Draw {(p.prob_draw * 100).toFixed(0)}% · xG{" "}
                    {p.xg_home?.toFixed(2)}–{p.xg_away?.toFixed(2)}
                </div>
            )}
        </button>
    );
}

function TeamRow({ code, pct, xg, isWinner, color }) {
    const bar = Math.max(4, Math.round((pct || 0) * 100));
    const barColor = color === "volt" ? "bg-volt" : "bg-signal";
    return (
        <div className="mb-1 flex items-center gap-2">
            <span
                className="w-6 text-lg leading-none"
                aria-hidden="true"
            >
                {flagEmoji(codeToFlag(code))}
            </span>
            <div className="min-w-0 flex-1">
                <div className="flex items-baseline justify-between">
                    <span
                        className={`font-display text-sm font-bold tracking-tight ${
                            isWinner ? "text-ink" : "text-mutedink"
                        }`}
                    >
                        {code || "TBD"}
                    </span>
                    <span
                        className={`font-mono text-[11px] tabular-nums ${
                            isWinner ? "text-ink" : "text-mutedink"
                        }`}
                    >
                        {pct !== undefined
                            ? `${(pct * 100).toFixed(0)}%`
                            : "—"}
                    </span>
                </div>
                <div className="mt-1 h-1 w-full overflow-hidden rounded-full bg-cream-strong">
                    <div
                        className={`prob-bar-fill h-full ${barColor}`}
                        style={{ "--fill": `${bar}%` }}
                    />
                </div>
            </div>
        </div>
    );
}

// tiny helper so bracket doesn't need to fetch team objects to render flags
const FLAG_MAP = {
        ARG: "AR", FRA: "FR", BRA: "BR", ESP: "ES", ENG: "GB", POR: "PT",
    BEL: "BE", COL: "CO", NOR: "NO", USA: "US", MAR: "MA", MEX: "MX",
    SUI: "CH", PAR: "PY", EGY: "EG", CAN: "CA",
};
function codeToFlag(code) {
    return FLAG_MAP[code] || "";
}
