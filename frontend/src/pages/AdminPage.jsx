import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, getBracket } from "../lib/api";
import { ArrowLeft, Trash, CheckCircle } from "@phosphor-icons/react";
import { toast } from "sonner";

export default function AdminPage() {
    const [key, setKey] = useState(localStorage.getItem("ms_admin_key") || "");
    const [authed, setAuthed] = useState(false);
    const [bracket, setBracket] = useState(null);
    const [results, setResults] = useState({});
    const [loading, setLoading] = useState(false);

    async function unlock() {
        setLoading(true);
        try {
            const r = await api.get("/admin/results", { headers: { "X-Admin-Key": key } });
            localStorage.setItem("ms_admin_key", key);
            const map = {};
            (r.data.results || []).forEach((x) => (map[x.match_id] = x.winner_code));
            setResults(map);
            setAuthed(true);
            const b = await getBracket();
            setBracket(b);
            toast.success("Admin unlocked");
        } catch (e) {
            toast.error("Invalid admin key");
            setAuthed(false);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        if (key && !authed) unlock();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    async function markWinner(match_id, winner_code) {
        try {
            await api.post("/admin/results", { match_id, winner_code }, { headers: { "X-Admin-Key": key } });
            setResults({ ...results, [match_id]: winner_code });
            const b = await getBracket();
            setBracket(b);
            toast.success(`${match_id} → ${winner_code}`);
        } catch (e) {
            toast.error("Failed to mark result");
        }
    }

    async function clearResult(match_id) {
        try {
            await api.delete(`/admin/results/${match_id}`, { headers: { "X-Admin-Key": key } });
            const { [match_id]: _drop, ...rest } = results;
            setResults(rest);
            const b = await getBracket();
            setBracket(b);
            toast.success(`${match_id} cleared`);
        } catch (e) {
            toast.error("Failed to clear result");
        }
    }

    if (!authed) {
        return (
            <div className="mx-auto max-w-md px-6 py-24">
                <Link to="/" className="focus-ring inline-flex items-center gap-2 rounded-md border border-hairline bg-canvas px-3 py-1.5 text-xs text-ink hover:border-coral">
                    <ArrowLeft size={12} weight="bold" /> Dashboard
                </Link>
                <h1 className="mt-8 font-display text-4xl tracking-tight text-ink">Admin</h1>
                <p className="mt-2 text-sm text-mutedink">Mark real results as the tournament progresses. Frozen matches propagate through the bracket, Monte Carlo, and Report Card.</p>
                <input
                    data-testid="admin-key-input"
                    type="password"
                    value={key}
                    onChange={(e) => setKey(e.target.value)}
                    placeholder="Admin key"
                    className="focus-ring mt-6 w-full rounded-md border border-hairline bg-canvas px-3 py-2.5 text-sm text-ink placeholder:text-mutedink"
                />
                <button
                    data-testid="admin-unlock"
                    onClick={unlock}
                    disabled={loading || !key}
                    className="focus-ring mt-3 w-full rounded-md bg-coral px-5 py-2.5 text-sm font-medium text-white hover:bg-coral-active disabled:opacity-60"
                >
                    {loading ? "Verifying…" : "Unlock admin"}
                </button>
            </div>
        );
    }

    if (!bracket) return <div className="p-10 text-mutedink">Loading bracket…</div>;

    const rounds = ["R16", "QF", "SF", "F"];
    const byRound = rounds.map((r) => bracket.matches.filter((m) => m.round === r));

    return (
        <div className="mx-auto max-w-[1100px] px-6 py-10 sm:px-10">
            <div className="flex items-center justify-between">
                <Link to="/" className="focus-ring inline-flex items-center gap-2 rounded-md border border-hairline bg-canvas px-3 py-1.5 text-xs text-ink hover:border-coral">
                    <ArrowLeft size={12} weight="bold" /> Dashboard
                </Link>
                <span className="text-[11px] uppercase tracking-widest text-mutedink">Admin · {Object.keys(results).length} results frozen</span>
            </div>
            <h1 className="mt-6 font-display text-4xl tracking-tight text-ink">Result Editor</h1>
            <p className="mt-2 max-w-2xl text-sm text-mutedink">Click a team to mark them as the actual winner of that match. Downstream QF/SF/F predictions reflow instantly.</p>

            <div className="mt-8 space-y-8">
                {rounds.map((r, i) => (
                    <div key={r}>
                        <div className="mb-3 text-[11px] uppercase tracking-widest text-mutedink">{r === "F" ? "Final" : r === "SF" ? "Semi-finals" : r === "QF" ? "Quarter-finals" : "Round of 16"}</div>
                        <div className="space-y-2">
                            {byRound[i].map((m) => {
                                const actual = results[m.id];
                                return (
                                    <div
                                        key={m.id}
                                        data-testid={`admin-match-${m.id}`}
                                        className={`flex items-center gap-3 rounded-md border p-3 ${actual ? "border-coral/40 bg-coral/[0.04]" : "border-hairline bg-cream-card"}`}
                                    >
                                        <div className="w-20 font-mono text-[10px] uppercase tracking-widest text-mutedink">{m.id}</div>
                                        <button
                                            data-testid={`admin-pick-${m.id}-home`}
                                            onClick={() => markWinner(m.id, m.home)}
                                            className={`focus-ring rounded-md px-3 py-2 text-sm font-medium ${actual === m.home ? "bg-coral text-white" : "border border-hairline bg-canvas text-ink hover:border-coral"}`}
                                        >
                                            {m.home}
                                        </button>
                                        <span className="text-xs text-mutedink">vs</span>
                                        <button
                                            data-testid={`admin-pick-${m.id}-away`}
                                            onClick={() => markWinner(m.id, m.away)}
                                            className={`focus-ring rounded-md px-3 py-2 text-sm font-medium ${actual === m.away ? "bg-coral text-white" : "border border-hairline bg-canvas text-ink hover:border-coral"}`}
                                        >
                                            {m.away}
                                        </button>
                                        <div className="flex-1" />
                                        {actual && (
                                            <>
                                                <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-widest text-coral">
                                                    <CheckCircle size={12} weight="fill" /> Final · {actual}
                                                </span>
                                                <button
                                                    data-testid={`admin-clear-${m.id}`}
                                                    onClick={() => clearResult(m.id)}
                                                    className="focus-ring rounded-md p-1.5 text-mutedink hover:text-signal"
                                                    aria-label={`Clear ${m.id} result`}
                                                >
                                                    <Trash size={14} />
                                                </button>
                                            </>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
