import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { CloudArrowDown } from "@phosphor-icons/react";

export default function LiveSyncBadge() {
    const [data, setData] = useState(null);
    useEffect(() => {
        api.get("/live/fixtures").then((r) => setData(r.data)).catch(() => {});
    }, []);
    if (!data) return null;
    const src = data.source;
    const label = src === "api_football" ? "API-Football · live" : src === "cache" ? "API-Football · cached" : "Mock dataset";
    const time = data.last_synced ? new Date(data.last_synced).toLocaleString("en-US", { hour12: false }) : "—";
    return (
        <div data-testid="live-sync-badge" className="inline-flex items-center gap-2 rounded-full border border-hairline bg-cream-card px-3 py-1 text-[10px] uppercase tracking-widest text-mutedink">
            <CloudArrowDown size={12} weight="bold" />
            <span>{label}</span>
            <span className="text-ink/60">·</span>
            <span>Last sync {time}</span>
        </div>
    );
}
