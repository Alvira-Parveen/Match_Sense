import React from "react";
import { Link } from "react-router-dom";
import { SoccerBall, Broadcast, Archive } from "@phosphor-icons/react";

export default function TopBar({ onOpenLogs }) {
    return (
        <header data-testid="top-bar" className="sticky top-0 z-40 border-b border-hairline bg-canvas/95 backdrop-blur">
            <div className="mx-auto flex max-w-[1200px] items-center justify-between px-6 py-4 sm:px-10">
                <div className="flex items-center gap-3">
                    <span className="text-ink text-xl leading-none">✳</span>
                    <div>
                        <div className="font-display text-2xl leading-none text-ink">
                            Match<span className="text-coral">Sense</span>
                        </div>
                        <div className="mt-0.5 text-[11px] text-mutedink">Agentic · WC 2026 · Knockout</div>
                    </div>
                </div>
                <div className="hidden items-center gap-6 md:flex">
                    <Link
                        to="/archive"
                        data-testid="nav-archive"
                        className="focus-ring flex items-center gap-2 rounded-md px-2 py-1.5 text-xs font-medium text-ink transition-colors hover:text-coral"
                    >
                        <Archive size={14} weight="bold" /> Archive
                    </Link>
                    <div className="flex items-center gap-2 text-xs text-mutedink">
                        <span className="relative flex h-2 w-2">
                            <span className="absolute inline-flex h-full w-full animate-pulse-dot rounded-full bg-success" />
                            <span className="relative inline-flex h-2 w-2 rounded-full bg-success" />
                        </span>
                        Agent Live
                    </div>
                    <button
                        data-testid="toggle-agent-logs"
                        onClick={onOpenLogs}
                        className="focus-ring flex items-center gap-2 rounded-md border border-hairline bg-canvas px-3 py-1.5 text-xs font-medium text-ink hover:border-coral hover:text-coral transition-colors"
                    >
                        <Broadcast size={14} weight="bold" /> Agent Logs
                    </button>
                </div>
            </div>
        </header>
    );
}
