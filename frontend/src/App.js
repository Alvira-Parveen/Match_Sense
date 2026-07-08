import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";

import TopBar from "@/components/TopBar";
import Hero from "@/components/Hero";
import Bracket from "@/components/Bracket";
import ChampionshipLeaderboard from "@/components/ChampionshipLeaderboard";
import AgentLogs from "@/components/AgentLogs";
import MatchDetailDialog from "@/components/MatchDetailDialog";
import ModelReportCard from "@/components/ModelReportCard";
import ThirdPlaceCard from "@/components/ThirdPlaceCard";
import TeamPage from "@/pages/TeamPage";
import AdminPage from "@/pages/AdminPage";
import ResultsArchivePage from "@/pages/ResultsArchivePage";
import LiveSyncBadge from "@/components/LiveSyncBadge";

import {
    getBracket,
    getSimulation,
    getAgentLogs,
    setFavorite,
    getFavorite,
} from "@/lib/api";
import { toast } from "sonner";

function getSessionId() {
    let s = localStorage.getItem("ms_session");
    if (!s) {
        s = "s-" + Math.random().toString(36).slice(2) + Date.now().toString(36);
        localStorage.setItem("ms_session", s);
    }
    return s;
}

function Home() {
    const [bracket, setBracketData] = useState(null);
    const [simulation, setSimulation] = useState(null);
    const [logs, setLogs] = useState([]);
    const [selectedMatch, setSelectedMatch] = useState(null);
    const [dialogOpen, setDialogOpen] = useState(false);
    const [favoriteTeam, setFavoriteTeam] = useState(null);
    const sessionId = getSessionId();

    useEffect(() => {
        getBracket().then(setBracketData).catch(() => {
            /* backend not ready */
        });
        getSimulation(10000).then(setSimulation).catch(() => {
            /* backend not ready */
        });
        getFavorite(sessionId)
            .then((r) => r.team && setFavoriteTeam(r.team.code))
            .catch(() => {
                /* no favorite yet */
            });
    }, [sessionId]);

    // poll logs every 4s
    useEffect(() => {
        let cancelled = false;
        async function tick() {
            try {
                const d = await getAgentLogs();
                if (!cancelled) setLogs(d.logs || []);
            } catch (_e) {
                /* poll error — retry next tick */
            }
        }
        tick();
        const t = setInterval(tick, 4000);
        return () => {
            cancelled = true;
            clearInterval(t);
        };
    }, []);

    function openMatch(m) {
        setSelectedMatch(m);
        setDialogOpen(true);
    }

    async function toggleFavorite(code) {
        const next = favoriteTeam === code ? null : code;
        setFavoriteTeam(next);
        try {
            if (next) {
                await setFavorite(sessionId, next);
                toast.success(`Following ${code}`, {
                    description: "Their bracket path is highlighted.",
                });
            }
        } catch (_e) {
            /* silent failure — favorite is optional */
        }
    }

    function scrollToLogs() {
        const el = document.querySelector('[data-testid="agent-logs-section"]');
        el?.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    const champ = simulation?.teams?.[0];

    return (
        <div className="grain min-h-screen bg-surface0 text-ink">
            <TopBar onOpenLogs={scrollToLogs} />

            <main>
                <Hero championPick={champ} />
                <Bracket
                    bracket={bracket}
                    onSelectMatch={openMatch}
                    favoriteTeam={favoriteTeam}
                />
                <ThirdPlaceCard bracket={bracket} onSelect={openMatch} />
                <ChampionshipLeaderboard
                    simulation={simulation}
                    favoriteTeam={favoriteTeam}
                    onToggleFavorite={toggleFavorite}
                />
                <ModelReportCard />
                <AgentLogs logs={logs} />
            </main>

            <footer className="border-t border-hairline py-8 text-center">
                <div className="mb-3 flex justify-center"><LiveSyncBadge /></div>
                <div className="font-mono text-[10px] uppercase tracking-widest text-mutedink">
                    MatchSense · Built by Alvira · FIFA WC 2026 knockout intelligence
                </div>
            </footer>

            <MatchDetailDialog
                open={dialogOpen}
                match={selectedMatch}
                onOpenChange={setDialogOpen}
            />

            <Toaster
                theme="dark"
                position="top-right"
                toastOptions={{
                    style: {
                        background: "#121212",
                        border: "1px solid #1e1e1e",
                        color: "#fff",
                    },
                }}
            />
        </div>
    );
}

export default function App() {
    return (
        <div className="App">
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/team/:code" element={<TeamShell />} />
                    <Route path="/admin" element={<AdminShell />} />
                    <Route path="/archive" element={<ArchiveShell />} />
                </Routes>
            </BrowserRouter>
        </div>
    );
}

function TeamShell() {
    return (
        <div className="grain min-h-screen bg-surface0 text-ink">
            <TopBar onOpenLogs={() => window.scrollTo({ top: 0 })} />
            <TeamPage />
        </div>
    );
}

function AdminShell() {
    return (
        <div className="grain min-h-screen bg-surface0 text-ink">
            <TopBar onOpenLogs={() => window.scrollTo({ top: 0 })} />
            <AdminPage />
            <Toaster theme="light" position="top-right" toastOptions={{ style: { background: "#efe9de", border: "1px solid #e6dfd8", color: "#141413" } }} />
        </div>
    );
}

function ArchiveShell() {
    return (
        <div className="grain min-h-screen bg-surface0 text-ink">
            <TopBar onOpenLogs={() => window.scrollTo({ top: 0 })} />
            <ResultsArchivePage />
        </div>
    );
}
