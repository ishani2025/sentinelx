import { createFileRoute } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import { Check, ChevronDown, Loader2, ShieldAlert } from "lucide-react";
import { useEffect, useState } from "react";
import { MagneticButton, Mono, Panel, PageHeader } from "@/components/soc/primitives";
import { pipelineStages } from "@/lib/soc-data";

export const Route = createFileRoute("/investigations")({
  head: () => ({
    meta: [
      { title: "Incident Investigation · SentinelX SOC" },
      {
        name: "description",
        content:
          "Replay the full AI investigation pipeline for an incident: normalization, correlation, agents, risk, policy, response and verification.",
      },
      { property: "og:title", content: "Incident Investigation · SentinelX SOC" },
      {
        property: "og:description",
        content: "Stage-by-stage transparency into how SentinelX triaged and contained an incident.",
      },
    ],
  }),
  component: Investigation,
});

function Investigation() {
  const [progress, setProgress] = useState(3);
  const [open, setOpen] = useState<string | null>("correlation");

  useEffect(() => {
    const id = setInterval(
      () => setProgress((p) => (p < 10 ? p + 1 : p)),
      2200,
    );
    return () => clearInterval(id);
  }, []);

  return (
    <div className="mx-auto max-w-[1200px]">
      <PageHeader
        eyebrow="INC-4821 · prod-win-app-07"
        title="Credential access via LSASS memory dump"
        description="Pipeline replay from raw telemetry through containment. Every stage exposes its input, output, confidence and evidence."
      >
        <div className="flex gap-2">
          <MagneticButton>Export timeline</MagneticButton>
          <MagneticButton variant="neon">
            <ShieldAlert className="size-3.5" /> Approve containment
          </MagneticButton>
        </div>
      </PageHeader>

      <Panel className="mb-5 px-5 py-4">
        <div className="flex items-center justify-between">
          <Mono className="text-muted-foreground">pipeline progress</Mono>
          <Mono className="text-neon">
            {progress + 1}/{pipelineStages.length} stages
          </Mono>
        </div>
        <div className="mt-2.5 h-1.5 overflow-hidden rounded-full bg-elevated">
          <motion.div
            className="h-full rounded-full"
            style={{ background: "var(--gradient-neon)" }}
            animate={{ width: `${((progress + 1) / pipelineStages.length) * 100}%` }}
            transition={{ type: "spring", stiffness: 120, damping: 22 }}
          />
        </div>
      </Panel>

      <ol className="relative space-y-2 pl-6">
        <div className="absolute top-2 bottom-2 left-[9px] w-px bg-border" />
        <motion.div
          className="absolute left-[9px] w-px"
          style={{ background: "var(--gradient-neon)", top: 8 }}
          animate={{ height: `${((progress + 1) / pipelineStages.length) * 100}%` }}
          transition={{ type: "spring", stiffness: 90, damping: 20 }}
        />

        {pipelineStages.map((stage, i) => {
          const done = i < progress;
          const active = i === progress;
          const expanded = open === stage.key;
          return (
            <li key={stage.key} className="relative">
              <span className="absolute top-4 -left-[22px] grid size-4 place-items-center">
                {done ? (
                  <span className="grid size-4 place-items-center rounded-full bg-neon/20">
                    <Check className="size-2.5 text-neon" />
                  </span>
                ) : active ? (
                  <motion.span
                    animate={{ scale: [1, 1.25, 1] }}
                    transition={{ duration: 1.4, repeat: Infinity }}
                    className="size-3 rounded-full bg-neon"
                  />
                ) : (
                  <span className="size-2.5 rounded-full border border-border bg-background" />
                )}
              </span>

              <motion.button
                layout
                onClick={() => setOpen(expanded ? null : stage.key)}
                aria-expanded={expanded}
                className={`glass flex w-full items-center gap-3 rounded-xl px-4 py-3 text-left transition-colors ${
                  active ? "border-neon/40" : "hover:border-neon/25"
                }`}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">{stage.name}</span>
                    <Mono className="rounded border border-border px-1.5 py-0.5 text-muted-foreground">
                      {stage.module}/
                    </Mono>
                    {active && (
                      <Mono className="flex items-center gap-1 text-neon">
                        <Loader2 className="size-3 animate-spin" /> processing
                      </Mono>
                    )}
                  </div>
                  <p className="mt-0.5 truncate text-xs text-muted-foreground">{stage.summary}</p>
                </div>
                <Mono className="hidden text-muted-foreground sm:block">{stage.ms}ms</Mono>
                <Mono
                  className="w-10 text-right"
                  style={{ color: stage.confidence > 0.8 ? "var(--neon)" : "var(--warning)" }}
                >
                  {stage.confidence ? `${Math.round(stage.confidence * 100)}%` : "—"}
                </Mono>
                <motion.span animate={{ rotate: expanded ? 180 : 0 }}>
                  <ChevronDown className="size-4 text-muted-foreground" />
                </motion.span>
              </motion.button>

              <AnimatePresence initial={false}>
                {expanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                    className="overflow-hidden"
                  >
                    <div className="mt-2 grid gap-3 rounded-xl border border-border/70 bg-surface/60 p-4 lg:grid-cols-2">
                      <CodeBlock label="input" code={stage.input} />
                      <CodeBlock label="output" code={stage.output} />
                      <div className="lg:col-span-2">
                        <Mono className="text-muted-foreground">evidence</Mono>
                        <ul className="mt-2 flex flex-wrap gap-2">
                          {stage.evidence.length === 0 && (
                            <li className="text-xs text-muted-foreground">
                              No evidence yet — stage not reached.
                            </li>
                          )}
                          {stage.evidence.map((e) => (
                            <motion.li
                              key={e}
                              initial={{ opacity: 0, scale: 0.95 }}
                              animate={{ opacity: 1, scale: 1 }}
                              className="rounded-lg border border-border bg-elevated/60 px-2.5 py-1 text-[11px] text-foreground/80"
                            >
                              {e}
                            </motion.li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

function CodeBlock({ label, code }: { label: string; code: string }) {
  return (
    <div>
      <Mono className="text-muted-foreground">{label}</Mono>
      <pre className="mt-2 overflow-x-auto rounded-lg border border-border/70 bg-background/70 p-3 font-mono text-[11px] leading-relaxed text-cyan/90">
        {code}
      </pre>
    </div>
  );
}