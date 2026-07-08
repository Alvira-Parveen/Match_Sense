import React, { useEffect, useRef, useState } from "react";
import { Play, Pause, TextAa, SpeakerHigh, ArrowsClockwise } from "@phosphor-icons/react";
import { getAudioSummary } from "../lib/api";

export default function AudioBriefingPlayer({ matchId, summary }) {
    const [audio, setAudio] = useState(null); // base64
    const [loading, setLoading] = useState(false);
    const [playing, setPlaying] = useState(false);
    const [largeText, setLargeText] = useState(false);
    const [lang, setLang] = useState("en");
    const [translated, setTranslated] = useState(null);
    const [error, setError] = useState("");
    const audioRef = useRef(null);

    async function loadAudio() {
        setLoading(true);
        setError("");
        setAudio(null);
        setTranslated(null);
        try {
            // omit voice so backend selects the language-native voice
            const url = `/audio-summary/${matchId}?lang=${lang}`;
            const { data } = await (await import("../lib/api")).api.get(url);
            if (data.audio_available && data.audio_base64) {
                setAudio(`data:audio/mp3;base64,${data.audio_base64}`);
            } else {
                setError("Audio narration unavailable. Text brief still readable below.");
            }
            if (data.summary_text) setTranslated(data.summary_text);
        } catch (e) {
            setError("Failed to generate audio. Try again.");
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        setAudio(null);
        setPlaying(false);
        setTranslated(null);
        setError("");
    }, [matchId, lang]);

    function togglePlay() {
        const el = audioRef.current;
        if (!el) return;
        if (playing) {
            el.pause();
        } else {
            el.play();
        }
    }

    return (
        <div
            data-testid="audio-briefing"
            className="rounded-sm border border-electric/30 bg-electric/[0.03] p-5"
            role="region"
            aria-label="Accessible audio briefing"
        >
            <div className="mb-3 flex items-center justify-between gap-3">
                <div>
                    <div className="font-mono text-[10px] uppercase tracking-[0.25em] text-electric">
                        Layer 3 · Accessibility
                    </div>
                    <h3 className="mt-1 font-display text-xl font-bold tracking-tight">
                        Audio Match Brief
                    </h3>
                </div>
                <div className="flex items-center gap-2">
                    <select
                        data-testid="lang-select"
                        aria-label="Choose narration language"
                        value={lang}
                        onChange={(e) => setLang(e.target.value)}
                        className="focus-ring rounded-sm border border-hairline bg-black px-2 py-2 font-mono text-[10px] uppercase tracking-[0.15em] text-bodytext hover:border-electric"
                    >
                        <option value="en">EN</option>
                        <option value="es">ES</option>
                        <option value="pt">PT</option>
                        <option value="fr">FR</option>
                    </select>
                    <button
                        data-testid="toggle-large-text"
                        onClick={() => setLargeText((v) => !v)}
                        aria-pressed={largeText}
                        className="focus-ring flex items-center gap-2 rounded-sm border border-hairline px-3 py-2 font-mono text-[10px] uppercase tracking-[0.2em] text-bodytext transition-colors hover:border-electric hover:text-electric"
                    >
                        <TextAa size={16} weight="bold" />
                        {largeText ? "Standard text" : "Large text"}
                    </button>
                </div>
            </div>

            <div className="flex items-center gap-3">
                {!audio ? (
                    <button
                        data-testid="generate-audio-button"
                        onClick={loadAudio}
                        disabled={loading}
                        aria-label="Generate audio briefing"
                        className="focus-ring flex h-12 min-w-[3rem] items-center gap-3 rounded-sm bg-volt px-5 font-display text-sm font-bold tracking-tight text-black transition-opacity hover:opacity-90 disabled:opacity-60"
                    >
                        {loading ? (
                            <ArrowsClockwise size={20} weight="bold" className="animate-spin" />
                        ) : (
                            <SpeakerHigh size={20} weight="bold" />
                        )}
                        {loading ? "Synthesising…" : "Generate audio"}
                    </button>
                ) : (
                    <button
                        data-testid="play-audio-button"
                        onClick={togglePlay}
                        aria-label={playing ? "Pause audio briefing" : "Play audio briefing"}
                        className="focus-ring flex h-12 w-12 items-center justify-center rounded-sm bg-volt text-black transition-opacity hover:opacity-90"
                    >
                        {playing ? <Pause size={22} weight="fill" /> : <Play size={22} weight="fill" />}
                    </button>
                )}
                <div className="flex-1 text-xs text-mutedink">
                    Native voice per language · OpenAI TTS · &lt;90 word narration generated from the Claude match brief.
                </div>
            </div>

            {audio && (
                <audio
                    ref={audioRef}
                    src={audio}
                    onPlay={() => setPlaying(true)}
                    onPause={() => setPlaying(false)}
                    onEnded={() => setPlaying(false)}
                    className="hidden"
                    aria-hidden="true"
                />
            )}

            {error && (
                <div
                    data-testid="audio-error"
                    role="alert"
                    className="mt-3 rounded-sm border border-signal/40 bg-signal/10 px-3 py-2 text-xs text-signal"
                >
                    {error}
                </div>
            )}

            <div
                data-testid="brief-summary-text"
                className={`mt-5 border-t border-hairline pt-4 leading-relaxed text-ink ${
                    largeText ? "text-2xl leading-relaxed" : "text-base"
                }`}
            >
                {translated || summary || "Loading match brief…"}
            </div>
        </div>
    );
}
