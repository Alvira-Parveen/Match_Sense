import React from "react";

export default function Hero({ championPick }) {
    return (
        <section data-testid="hero-section" className="border-b border-hairline">
            <div className="mx-auto grid max-w-[1200px] gap-16 px-6 py-20 sm:px-10 sm:py-28 lg:grid-cols-12">
                <div className="lg:col-span-7">
                    <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-hairline bg-cream-card px-3 py-1">
                        <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-coral" />
                        <span className="text-[11px] font-medium text-ink">FIFA World Cup 2026 · Round of 16 → Final</span>
                    </div>
                    <h1 data-testid="hero-heading" className="font-display text-5xl leading-[1.05] tracking-tight text-ink sm:text-6xl lg:text-7xl">
                        Your thinking partner<br />for the knockout stage.
                    </h1>
                    <p className="mt-8 max-w-xl text-lg leading-relaxed text-bodytext">
                        An autonomous agent gathers match intelligence. A real XGBoost model — trained on 900 historical knockouts — predicts with 81.4% replay accuracy. A ten-thousand-run Monte Carlo simulation surfaces championship odds. And every brief is narrated aloud, in four languages, for fans who cannot see the screen.
                    </p>
                    <div className="mt-10 flex flex-wrap items-center gap-3">
                        <a href="#bracket" data-testid="hero-cta-bracket" className="focus-ring rounded-md bg-coral px-5 py-3 text-sm font-medium text-white hover:bg-coral-active transition-colors">
                            Explore the bracket
                        </a>
                        <a href="#report" data-testid="hero-cta-report" className="focus-ring rounded-md border border-hairline bg-canvas px-5 py-3 text-sm font-medium text-ink hover:border-ink transition-colors">
                            See the model's report card
                        </a>
                    </div>
                    {championPick && (
                        <div data-testid="hero-champion-pick" className="mt-10 inline-flex items-center gap-4 rounded-md border border-hairline bg-cream-card px-5 py-3">
                            <span className="text-[11px] uppercase tracking-wider text-mutedink">Model&apos;s current champion pick</span>
                            <span className="font-display text-2xl text-ink">
                                {championPick.name} <span className="text-coral">{(championPick.prob_champion * 100).toFixed(1)}%</span>
                            </span>
                        </div>
                    )}
                </div>
                <div className="lg:col-span-5">
                    <div className="rounded-xl bg-navy p-8 text-on-dark shadow-sm">
                        <div className="mb-4 flex items-center gap-2">
                            <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f56]" />
                            <span className="h-2.5 w-2.5 rounded-full bg-[#ffbd2e]" />
                            <span className="h-2.5 w-2.5 rounded-full bg-[#27c93f]" />
                            <span className="ml-3 font-mono text-[11px] text-[#a09d96]">matchsense · agent trace</span>
                        </div>
                        <pre className="whitespace-pre-wrap font-mono text-[13px] leading-relaxed text-[#faf9f5]">
{`> agent.run("R16-M7")
  ✓ fetch_fixture     ARG vs EGY · Mercedes-Benz
  ✓ form_and_h2h      form: WWWDW / WWDDL
  ✓ injury_report     1 doubt · 0 out
  ✓ xgb.predict       home 0.71 · draw 0.12
  ✓ tts.synthesize    nova · 780ms
  ✓ log → mongo       persisted

briefing ready.`}
                        </pre>
                    </div>
                </div>
            </div>
        </section>
    );
}
