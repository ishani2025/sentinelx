import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Bot } from "lucide-react";
import { useEffect, useState } from "react";
import { Mono, Panel, PageHeader } from "@/components/soc/primitives";
import { agents } from "@/lib/soc-data";

export const Route = createFileRoute("/agents")({
  head: () => ({
    meta: [
      { title: "AI Agents · SentinelX SOC" },
      {
        name: "description",
        content:
          "Monitor SentinelX supervisor and specialist agents: reasoning state, confidence, tool usage and decision graph.",
      },
      { property: "og:title", content: "AI Agents · SentinelX SOC" },
      {
        property: "og:description",
        content: "Supervisor orchestration, specialist agents and live confidence metering.",
      },
    ],
  }),
  component: AgentsPage,
});

function AgentsPage() {
  return (
    <div className="mx-auto max-w-[1200px]">
      <PageHeader
        eyebrow="agents/"
        title="Agent mesh"
        description="Supervisor delegates to specialist agents with token budgets. Confidence is recomputed after every tool call."
      />
      <div className="grid gap-5 lg:grid-cols-2">
        {agents.map((a, i) => (
          <Panel key={a.name} className="p-5" transition={{ delay: i * 0.07, duration: 0.4 }}>
            <div className="flex items-start gap-3">
              <motion.span
                animate={
                  a.state === "thinking"
                    ? { boxShadow: ["0 0 0 var(--neon)", "0 0 22px var(--neon)", "0 0 0 var(--neon)"] }
                    : {}
                }
                transition={{ duration: 2.2, repeat: Infinity }}
                className="grid size-10 shrink-0 place-items-center rounded-xl bg-neon/12"
              >
                <Bot className="size-5 text-neon" />
              </motion.span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold">{a.name} agent</h3>
                  <Mono
                    className="rounded border px-1.5 py-0.5"
                    style={{
                      color: a.state === "thinking" ? "var(--neon)" : "var(--muted-foreground)",
                    }}
                  >
                    {a.state}
                  </Mono>
                </div>
                <p className="mt-0.5 text-xs text-muted-foreground">{a.role}</p>
              </div>
            </div>

            <div className="mt-4">
              <div className="flex items-center justify-between">
                <Mono className="text-muted-foreground">confidence</Mono>
                <Mono className="text-cyan">{Math.round(a.confidence * 100)}%</Mono>
              </div>
              <div className="mt-1.5 h-1.5 rounded-full bg-elevated">
                <motion.div
                  className="h-1.5 rounded-full"
                  style={{ background: "var(--gradient-neon)" }}
                  initial={{ width: 0 }}
                  animate={{ width: `${a.confidence * 100}%` }}
                  transition={{ duration: 1, delay: 0.15 + i * 0.06 }}
                />
              </div>
            </div>

            <div className="mt-4 rounded-xl border border-border/70 bg-background/60 p-3">
              <Mono className="text-muted-foreground">reasoning trace</Mono>
              <Typewriter text={a.thought} />
            </div>
          </Panel>
        ))}
      </div>
    </div>
  );
}

function Typewriter({ text }: { text: string }) {
  const [n, setN] = useState(0);
  useEffect(() => {
    setN(0);
    const id = setInterval(() => setN((v) => (v >= text.length ? 0 : v + 1)), 42);
    return () => clearInterval(id);
  }, [text]);
  return (
    <p className="mt-1.5 font-mono text-[11px] leading-relaxed text-foreground/80">
      {text.slice(0, n)}
      <motion.span
        animate={{ opacity: [1, 0] }}
        transition={{ duration: 0.6, repeat: Infinity }}
        className="ml-0.5 inline-block h-3 w-1.5 translate-y-0.5 bg-neon"
      />
    </p>
  );
}