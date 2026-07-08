import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getTeamDetail, flagEmoji } from "../lib/api";
import { ArrowLeft, MedalMilitary, Bandaids, Users, TrendUp } from "@phosphor-icons/react";

const ROUND_TITLES = {
    R16: "Round of 16",
    QF: "Quarter-final",
    SF: "Semi-final",
    F: "Final",
};

export default function TeamPage() {
    const { code } = useParams();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [err, setErr] = useState("");

    useEffect(() => {
        setLoading(true);
        getTeamDetail(code)
            .then(setData)
            .catch(() => setErr("Team not found"))
            .finally(() => setLoading(false));
    }, [code]);

    if (loading)
        return (
            <div className="mx-auto max-w-3xl px-6 py-20 font-mono text-xs uppercase tracking-[0.2em] text-slate-500">
                Loading team dossier…
            </div>
        );
    if (err || !data)
        return (
            <div className="mx-auto max-w-3xl px-6 py-20">
                <div className="text-signal">{err || "Team not found"}</div>
                <Link
                    to="/"
                    className="mt-4 inline-flex items-center gap-2 text-volt hover:underline"
                >
                    <ArrowLeft /> Back to dashboard
                </Link>
            </div>
        );

    const { team, championship, predicted_path, advances_to_champion } = data;

    return (
        <div
            data-testid={`team-page-${code}`}
            className="mx-auto max-w-[1100px] px-6 py-10 sm:px-10"
        >
            <Link
                to="/"
                className="focus-ring inline-flex items-center gap-2 rounded-sm border border-white/10 px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-400 hover:border-volt hover:text-volt"
            >
                <ArrowLeft size={12} weight="bold" /> Dashboard
            </Link>

            <div className="mt-8 flex flex-col items-start gap-6 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-5">
                    <span className="text-6xl">{flagEmoji(team.flag)}</span>
                    <div>
                        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
                            {team.confed} · ELO {team.elo}
                        </div>
                        <h1 className="mt-1 font-display text-5xl font-black uppercase tracking-tighter">
                            {team.name}
                        </h1>
                        <div className="mt-1 text-sm text-slate-400">
                            Star: {team.star}
                        </div>
                    </div>
                </div>
                {championship && (
                    <div
                        data-testid="team-champ-prob"
                        className={`rounded-sm border p-4 text-center ${
                            advances_to_champion
                                ? "border-electric/60 bg-electric/10"
                                : "border-white/10 bg-surface1"
                        }`}
                    >
                        <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                            Championship probability
                        </div>
                        <div className="mt-1 font-display text-4xl font-black tabular-nums text-volt">
                            {(championship.prob_champion * 100).toFixed(1)}%
                        </div>
                        {advances_to_champion && (
                            <div className="mt-1 flex items-center justify-center gap-1 font-mono text-[10px] uppercase tracking-[0.2em] text-electric">
                                <MedalMilitary size={12} weight="fill" />{" "}
                                Model's champion pick
                            </div>
                        )}
                    </div>
                )}
            </div>

            {championship && (
                <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
                    <Stat label="Reach QF" value={`${(championship.prob_qf * 100).toFixed(0)}%`} />
                    <Stat label="Reach SF" value={`${(championship.prob_sf * 100).toFixed(0)}%`} />
                    <Stat label="Reach Final" value={`${(championship.prob_final * 100).toFixed(1)}%`} />
                    <Stat label="Champion" value={`${(championship.prob_champion * 100).toFixed(1)}%`} highlight />
                </div>
            )}

            <div className="mt-10 grid gap-6 lg:grid-cols-3">
                <Card icon={<TrendUp className="text-volt" />} title="Recent Form">
                    <div className="mt-2 flex gap-1.5">
                        {team.form.split("").map((r, i) => (
                            <span
                                key={i}
                                className={`inline-flex h-8 w-8 items-center justify-center rounded-sm font-mono text-sm font-bold ${
                                    r === "W"
                                        ? "bg-success/20 text-success"
                                        : r === "D"
                                        ? "bg-slate-500/20 text-slate-300"
                                        : "bg-signal/20 text-signal"
                                }`}
                            >
                                {r}
                            </span>
                        ))}
                    </div>
                    <div className="mt-3 font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                        Attack {team.attack} · Defense {team.defense}
                    </div>
                </Card>

                <Card icon={<Bandaids className="text-signal" />} title="Injury feed">
                    {team.injuries.length === 0 ? (
                        <div className="mt-2 text-sm text-slate-400">
                            Squad reported near full strength.
                        </div>
                    ) : (
                        <ul className="mt-2 space-y-1 text-sm text-slate-300">
                            {team.injuries.map((i, idx) => (
                                <li key={idx} className="flex gap-2">
                                    <span className="text-signal">•</span> {i}
                                </li>
                            ))}
                        </ul>
                    )}
                </Card>

                <Card icon={<Users className="text-electric" />} title="Continental group">
                    <div className="mt-2 font-display text-2xl font-bold uppercase tracking-tight">
                        {team.confed}
                    </div>
                    <div className="mt-1 text-xs text-slate-400">
                        Represents the {team.confed} confederation at WC 2026.
                    </div>
                </Card>
            </div>

            <div className="mt-10">
                <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate-500">
                    Predicted tournament path
                </div>
                <h2 className="mt-1 font-display text-3xl font-black uppercase tracking-tight">
                    Road to the Final
                </h2>

                <div className="mt-4 space-y-3">
                    {predicted_path.length === 0 && (
                        <div className="text-sm text-slate-500">
                            No matches on the predicted path yet.
                        </div>
                    )}
                    {predicted_path.map((m) => {
                        const isHome = m.home === code.toUpperCase();
                        const p = m.prediction || {};
                        const winsHere = m.predicted_winner === code.toUpperCase();
                        const opponent = isHome ? m.away : m.home;
                        const ownPct = isHome ? p.prob_home : p.prob_away;
                        return (
                            <div
                                key={m.match_id}
                                data-testid={`path-${m.match_id}`}
                                className={`flex items-center justify-between rounded-sm border px-4 py-3 ${
                                    winsHere
                                        ? "border-volt/40 bg-volt/[0.04]"
                                        : "border-signal/40 bg-signal/[0.04]"
                                }`}
                            >
                                <div className="flex items-center gap-4">
                                    <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                                        {ROUND_TITLES[m.round]}
                                    </div>
                                    <div className="font-display text-lg font-bold uppercase tracking-tight">
                                        vs {opponent}
                                    </div>
                                </div>
                                <div className="flex items-center gap-4">
                                    <div className="font-mono text-xs tabular-nums text-slate-400">
                                        Win {((ownPct || 0) * 100).toFixed(0)}%
                                    </div>
                                    <span
                                        className={`rounded-sm px-2 py-1 font-mono text-[10px] font-bold uppercase tracking-[0.15em] ${
                                            winsHere
                                                ? "bg-volt/20 text-volt"
                                                : "bg-signal/20 text-signal"
                                        }`}
                                    >
                                        {winsHere ? "Advances" : "Eliminated"}
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}

function Stat({ label, value, highlight }) {
    return (
        <div
            className={`rounded-sm border p-4 ${
                highlight
                    ? "border-volt/40 bg-volt/[0.05]"
                    : "border-white/10 bg-surface1"
            }`}
        >
            <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                {label}
            </div>
            <div className="mt-1 font-display text-2xl font-black tabular-nums">
                {value}
            </div>
        </div>
    );
}

function Card({ icon, title, children }) {
    return (
        <div className="rounded-sm border border-white/10 bg-surface1 p-5">
            <div className="flex items-center gap-2">
                {icon}
                <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-slate-500">
                    {title}
                </div>
            </div>
            {children}
        </div>
    );
}
