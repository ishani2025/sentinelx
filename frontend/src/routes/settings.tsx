import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useState } from "react";
import { MagneticButton, Mono, PageHeader, TerminalCard } from "@/components/soc/primitives";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings · SentinelX SOC" },
      {
        name: "description",
        content:
          "Tune autonomy thresholds, agent budgets, approval gates and notification routing for the SentinelX SOC.",
      },
      { property: "og:title", content: "Settings · SentinelX SOC" },
      {
        property: "og:description",
        content: "Operator controls for autonomy level, approvals and agent runtime budgets.",
      },
    ],
  }),
  component: Settings,
});

const toggles = [
  { key: "auto_isolate", label: "Auto-isolate above risk 85", on: true, scope: "response/governor" },
  { key: "auto_disable", label: "Auto-disable identities", on: false, scope: "response/approval" },
  { key: "dry_run", label: "Dry-run before execution", on: true, scope: "agents/verification" },
  { key: "quiet_hours", label: "Suppress low severity 22:00–06:00", on: false, scope: "reporting" },
];

function Settings() {
  const [state, setState] = useState(() => Object.fromEntries(toggles.map((t) => [t.key, t.on])));
  const [autonomy, setAutonomy] = useState(72);

  return (
    <div className="mx-auto max-w-[1000px]">
      <PageHeader
        eyebrow="orchestrator/config"
        title="Operator settings"
        description="Changes are versioned and audited. Autonomy level defines how far the orchestrator may act before requesting a human gate."
      >
        <MagneticButton variant="neon">Save configuration</MagneticButton>
      </PageHeader>

      <TerminalCard label="autonomy level" className="mb-4 px-5 py-5">
        <div className="flex items-baseline gap-3">
          <span className="text-glow font-mono text-3xl font-bold">{autonomy}%</span>
          <Mono className="text-muted-foreground">
            {autonomy > 80 ? "fully autonomous containment" : autonomy > 50 ? "assisted containment" : "advisory only"}
          </Mono>
        </div>
        <input
          type="range"
          min={0}
          max={100}
          value={autonomy}
          aria-label="Autonomy level"
          onChange={(e) => setAutonomy(Number(e.target.value))}
          className="mt-4 w-full accent-[var(--neon)]"
        />
      </TerminalCard>

      <div className="grid gap-3 md:grid-cols-2">
        {toggles.map((t, i) => (
          <TerminalCard key={t.key} label={t.scope} delay={i * 0.07}>
            <div className="flex items-center justify-between gap-4">
              <span className="text-xs tracking-wide">{t.label}</span>
              <button
                role="switch"
                aria-checked={state[t.key]}
                aria-label={t.label}
                onClick={() => setState((s) => ({ ...s, [t.key]: !s[t.key] }))}
                className={`relative h-6 w-11 shrink-0 rounded-full border transition-colors ${
                  state[t.key] ? "border-neon/60 bg-neon/25" : "border-neon/20 bg-neon/5"
                }`}
              >
                <motion.span
                  layout
                  transition={{ type: "spring", stiffness: 500, damping: 32 }}
                  className="absolute top-1/2 size-4 -translate-y-1/2 rounded-full bg-neon shadow-[0_0_12px_var(--neon)]"
                  style={{ left: state[t.key] ? 24 : 4 }}
                />
              </button>
            </div>
          </TerminalCard>
        ))}
      </div>
    </div>
  );
}
