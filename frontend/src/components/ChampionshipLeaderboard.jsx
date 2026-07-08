import React from "react";
import { Link } from "react-router-dom";
import { flagEmoji } from "../lib/api";
import { Star, StarBold } from "../lib/icons";

export default function ChampionshipLeaderboard({
    simulation,
    favoriteTeam,
    onToggleFavorite,
}) {
    if (!simulation) return null;
    const top = simulation.teams.slice(0, 16);
    return (
        <section
            data-testid="leaderboard-section"
            aria-labelledby="lb-title"
            className="border-b border-hairline py-16"
        >
            <div className="mx-auto max-w-[1400px] px-6 sm:px-10">
                <div className="mb-8 flex items-end justify-between">
                    <div>
                        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-mutedink">
                            Monte Carlo · {simulation.runs.toLocaleString()}{" "}
                            iterations
                        </div>
                        <h2
                            id="lb-title"
                            className="mt-2 font-display text-3xl font-medium tracking-tight sm:text-4xl"
                        >
                            Championship Probability
                        </h2>
                    </div>
                </div>

                <div className="rounded-sm border border-hairline bg-cream-card">
                    <div className="grid grid-cols-12 border-b border-hairline px-4 py-3 font-mono text-[10px] uppercase tracking-[0.2em] text-mutedink">
                        <div className="col-span-1">#</div>
                        <div className="col-span-4">Team</div>
                        <div className="col-span-2 text-right">QF</div>
                        <div className="col-span-2 text-right">SF</div>
                        <div className="col-span-2 text-right">Final</div>
                        <div className="col-span-1 text-right">Champ</div>
                    </div>
                    {top.map((t, i) => {
                        const isFav = favoriteTeam === t.code;
                        return (
                            <div
                                key={t.code}
                                data-testid={`leaderboard-row-${t.code}`}
                                className={`grid grid-cols-12 items-center border-b border-hairline/60 px-4 py-3 last:border-b-0 transition-colors hover:bg-cream-card ${
                                    isFav ? "bg-electric/[0.06]" : ""
                                }`}
                            >
                                <div className="col-span-1 font-mono text-sm font-bold text-mutedink">
                                    {String(i + 1).padStart(2, "0")}
                                </div>
                                <div className="col-span-4 flex items-center gap-3">
                                    <button
                                        data-testid={`favorite-${t.code}`}
                                        aria-label={
                                            isFav
                                                ? `Remove ${t.name} from favorites`
                                                : `Set ${t.name} as favorite`
                                        }
                                        onClick={() => onToggleFavorite(t.code)}
                                        className="focus-ring rounded-sm p-1 text-mutedink transition-colors hover:text-electric"
                                    >
                                        {isFav ? (
                                            <StarBold
                                                className="text-electric"
                                                size={18}
                                            />
                                        ) : (
                                            <Star size={18} />
                                        )}
                                    </button>
                                    <span className="text-xl">
                                        {flagEmoji(t.flag)}
                                    </span>
                                    <div>
                                        <Link
                                            data-testid={`team-link-${t.code}`}
                                            to={`/team/${t.code}`}
                                            className="focus-ring rounded-sm font-display text-lg font-bold tracking-tight hover:text-volt"
                                        >
                                            {t.name}
                                        </Link>
                                        <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-mutedink">
                                            ELO {t.elo}
                                        </div>
                                    </div>
                                </div>
                                <div className="col-span-2 text-right font-mono text-sm tabular-nums text-mutedink">
                                    {(t.prob_qf * 100).toFixed(0)}%
                                </div>
                                <div className="col-span-2 text-right font-mono text-sm tabular-nums text-mutedink">
                                    {(t.prob_sf * 100).toFixed(0)}%
                                </div>
                                <div className="col-span-2 text-right font-mono text-sm tabular-nums text-bodytext">
                                    {(t.prob_final * 100).toFixed(1)}%
                                </div>
                                <div className="col-span-1 text-right">
                                    <span className="inline-block rounded-sm bg-volt/15 px-2 py-1 font-mono text-xs font-bold tabular-nums text-volt">
                                        {(t.prob_champion * 100).toFixed(1)}%
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </section>
    );
}
