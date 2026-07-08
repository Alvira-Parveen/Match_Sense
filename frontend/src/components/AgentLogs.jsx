import React from "react";
import { Terminal } from "@phosphor-icons/react";

const LEVEL_COLOR = {
    INFO: "text-volt",
    WARN: "text-electric",
    ERROR: "text-signal",
};

export default function AgentLogs({ logs, embedded = false }) {
    return (
        <section
            data-testid="agent-logs-section"
            aria-labelledby="logs-title"
            className={embedded ? "" : "border-b border-hairline py-16"}
        >
            <div className={embedded ? "" : "mx-auto max-w-[1400px] px-6 sm:px-10"}>
                {!embedded && (
                    <div className="mb-8">
                        <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-mutedink">
                            Layer 1 · Autonomous Agent
                        </div>
                        <h2
                            id="logs-title"
                            className="mt-2 font-display text-3xl font-medium tracking-tight sm:text-4xl"
                        >
                            Agent Activity Feed
                        </h2>
                    </div>
                )}
                <div className="rounded-sm border border-hairline bg-black">
                    <div className="flex items-center justify-between border-b border-hairline px-4 py-2.5">
                        <div className="flex items-center gap-2">
                            <Terminal size={14} className="text-volt" />
                            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-mutedink">
                                matchsense-agent · stdout
                            </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <span className="h-2 w-2 animate-pulse-dot rounded-full bg-success" />
                            <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-success">
                                online
                            </span>
                        </div>
                    </div>
                    <div
                        role="log"
                        aria-live="polite"
                        className="term-scroll max-h-72 overflow-y-auto p-4 font-mono text-xs leading-relaxed"
                    >
                        {(logs || []).length === 0 ? (
                            <div className="text-mutedink">
                                Waiting for agent events…
                            </div>
                        ) : (
                            logs.map((l, i) => (
                                <div
                                    key={i}
                                    data-testid={`log-line-${i}`}
                                    className="mb-1 flex gap-3"
                                >
                                    <span className="w-40 shrink-0 text-mutedink">
                                        {new Date(l.ts).toLocaleTimeString(
                                            "en-US",
                                            { hour12: false },
                                        )}
                                    </span>
                                    <span
                                        className={`w-14 shrink-0 font-bold ${
                                            LEVEL_COLOR[l.level] || "text-mutedink"
                                        }`}
                                    >
                                        {l.level}
                                    </span>
                                    <span className="w-24 shrink-0 text-mutedink">
                                        {l.tool}
                                    </span>
                                    <span className="text-bodytext">
                                        {l.message}
                                    </span>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </section>
    );
}
