import React, { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "./ui/dialog";
import { flagEmoji, getMatchBrief } from "../lib/api";
import SHAPPanel from "./SHAPPanel";
import AudioBriefingPlayer from "./AudioBriefingPlayer";
import { MapPin, Clock, Users, Bandaids } from "@phosphor-icons/react";

const ROUND_TITLES = {
    R16: "Round of 16",
    QF: "Quarter-final",
    SF: "Semi-final",
    F: "Final",
};

export default function MatchDetailDialog({ open, match, onOpenChange }) {
    const [brief, setBrief] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!open || !match) return;
        let cancelled = false;
        setBrief(null);
        setLoading(true);
        getMatchBrief(match.id)
            .then((b) => {
                if (!cancelled) setBrief(b);
            })
            .catch(() => {
                // ignore fetch failures — UI will show empty state
            });
        return () => {
            cancelled = true;
        };
    }, [open, match?.id]);

    if (!match) return null;

    const p = brief?.prediction || match.prediction || {};
    const homeFav = (p.prob_home || 0) >= (p.prob_away || 0);
    const homeName = brief?.fixture?.home || match.home;
    const awayName = brief?.fixture?.away || match.away;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent
                data-testid="match-detail-dialog"
                className="max-h-[92vh] overflow-y-auto border-hairline bg-cream-card p-0 sm:max-w-4xl"
            >
                <DialogTitle className="sr-only">
                    Match brief for {homeName} vs {awayName}
                </DialogTitle>
                <DialogDescription className="sr-only">
                    Ensemble prediction, SHAP explanation and audio briefing.
                </DialogDescription>

                <div className="border-b border-hairline px-6 pb-4 pt-6 sm:px-8">
                    <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-volt">
                        {ROUND_TITLES[match.round] || match.round} · {match.id}
                    </div>

                    <div className="mt-4 flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
                        <TeamBlock
                            code={match.home}
                            name={homeName}
                            pct={p.prob_home}
                            xg={p.xg_home}
                            fav={homeFav}
                            align="left"
                        />
                        <div className="text-center">
                            <div className="font-display text-4xl font-medium tracking-tighter text-mutedink">
                                VS
                            </div>
                            {p.prob_draw !== undefined && (
                                <div className="mt-2 font-mono text-[10px] uppercase tracking-[0.2em] text-mutedink">
                                    Draw {(p.prob_draw * 100).toFixed(0)}%
                                </div>
                            )}
                        </div>
                        <TeamBlock
                            code={match.away}
                            name={awayName}
                            pct={p.prob_away}
                            xg={p.xg_away}
                            fav={!homeFav}
                            align="right"
                        />
                    </div>

                    {brief && (
                        <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 font-mono text-[11px] uppercase tracking-[0.15em] text-mutedink">
                            <span className="flex items-center gap-1.5">
                                <MapPin size={12} /> {brief.fixture.venue}
                            </span>
                            <span className="flex items-center gap-1.5">
                                <Clock size={12} /> {brief.fixture.kickoff}
                            </span>
                        </div>
                    )}
                </div>

                <div className="grid gap-6 p-6 sm:grid-cols-2 sm:p-8">
                    <div className="space-y-6">
                        <AudioBriefingPlayer
                            matchId={match.id}
                            summary={
                                brief?.summary ||
                                (loading ? "Agent is preparing the brief…" : "")
                            }
                        />
                        {brief && <IntelBlocks brief={brief} />}
                    </div>
                    <div>
                        <SHAPPanel features={p.features || []} shap={p.shap || []} />
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}

function TeamBlock({ code, name, pct, xg, fav, align }) {
    const FLAG = {
            ARG: "AR", FRA: "FR", BRA: "BR", ESP: "ES", ENG: "GB", POR: "PT",
    BEL: "BE", COL: "CO", NOR: "NO", USA: "US", MAR: "MA", MEX: "MX",
    SUI: "CH", PAR: "PY", EGY: "EG", CAN: "CA",
    };
    return (
        <div className={`flex-1 ${align === "right" ? "sm:text-right" : "sm:text-left"}`}>
            <div className={`flex items-center gap-3 ${align === "right" ? "sm:justify-end" : ""}`}>
                <span className="text-4xl leading-none">{flagEmoji(FLAG[code])}</span>
                <div>
                    <div
                        className={`font-display text-3xl font-medium uppercase leading-none tracking-tight ${
                            fav ? "text-ink" : "text-mutedink"
                        }`}
                    >
                        {name || code}
                    </div>
                    <div className="mt-1 font-mono text-[10px] uppercase tracking-[0.2em] text-mutedink">
                        Win probability
                    </div>
                </div>
            </div>
            <div className={`mt-3 flex items-baseline gap-2 ${align === "right" ? "sm:justify-end" : ""}`}>
                <span
                    className={`font-display text-5xl font-medium tabular-nums ${
                        fav ? "text-volt" : "text-mutedink"
                    }`}
                >
                    {pct !== undefined ? (pct * 100).toFixed(0) : "—"}
                    <span className="text-2xl">%</span>
                </span>
                {xg !== undefined && (
                    <span className="font-mono text-xs tabular-nums text-mutedink">
                        xG {xg.toFixed(2)}
                    </span>
                )}
            </div>
        </div>
    );
}

function IntelBlocks({ brief }) {
    const inj = brief.injuries;
    return (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <IntelCard
                icon={<Users size={16} className="text-volt" />}
                label="Key players"
                lines={[
                    `${brief.fixture.home}: ${inj.home_star}`,
                    `${brief.fixture.away}: ${inj.away_star}`,
                ]}
            />
            <IntelCard
                icon={<Bandaids size={16} className="text-signal" />}
                label="Injury feed"
                lines={
                    (inj.home_injuries.length + inj.away_injuries.length)
                        ? [
                              ...inj.home_injuries.map((i) => `${brief.fixture.home}: ${i}`),
                              ...inj.away_injuries.map((i) => `${brief.fixture.away}: ${i}`),
                          ]
                        : ["Both squads reported near full strength."]
                }
            />
        </div>
    );
}

function IntelCard({ icon, label, lines }) {
    return (
        <div className="rounded-sm border border-hairline bg-black/40 p-3">
            <div className="mb-2 flex items-center gap-2 font-mono text-[10px] uppercase tracking-[0.2em] text-mutedink">
                {icon} {label}
            </div>
            <div className="space-y-1 text-xs text-bodytext">
                {lines.map((l, i) => (
                    <div key={i}>{l}</div>
                ))}
            </div>
        </div>
    );
}
