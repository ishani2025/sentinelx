import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Activity, RefreshCw } from "lucide-react";
import { MagneticButton, Mono, PageHeader, TerminalCard } from "@/components/soc/primitives";

export const Route = createFileRoute("/integrations")({
  head: () => ({
    meta: [
      { title: "Integrations · SentinelX SOC" },
      {
        name: "description",
        content:
          "Health, latency and delivery logs for SentinelX integrations: Slack, TheHive, Jira and ServiceNow.",
      },
      { property: "og:title", content: "Integrations · SentinelX SOC" },
      {
        property: "og:description",
        content: "Monitor connector health and outbound case delivery across the SOC tool chain.",
      },
    ],
  }),
  component: Integrations,
});

const connectors = [
  { name: "Slack", scope: "integrations/slack", status: "healthy", latency: 84, sent: 1284, log: "chat.postMessage 200 · #soc-critical" },
  { name: "TheHive", scope: "integrations/thehive", status: "healthy", latency: 212, sent: 318, log: "case/4821 created · severity 3" },
  { name: "Jira", scope: "integrations/jira", status: "degraded", latency: 940, sent: 96, log: "issue SEC-2210 retry 2/3 · 429" },
  { name: "ServiceNow", scope: "integrations/servicenow", status: "healthy", latency: 386, sent: 54, log: "INC0019283 change ticket linked" },
];

const tone = (s: string) => (s === "healthy" ? "var(--neon)" : "var(--warning)");

function Integrations() {
  return (
    <div className="mx-auto max-w-[1200px]">
      <PageHeader
        eyebrow="integrations/"
        title="Connector health"
        description="Every outbound action from the response engine is delivered through these connectors. Latency and delivery state are sampled every 15 seconds."
      >
        <MagneticButton variant="neon">
          <RefreshCw className="size-3.5" /> Reconnect all
        </MagneticButton>
      </PageHeader>

      <div className="grid gap-4 md:grid-cols-2">
        {connectors.map((c, i) => (
          <TerminalCard key={c.name} label={c.scope} delay={i * 0.08} className="px-5 py-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-glow font-mono text-lg font-bold tracking-widest uppercase">
                  {c.name}
                </p>
                <Mono className="mt-1 block" style={{ color: tone(c.status) }}>
                  ● {c.status}
                </Mono>
              </div>
              <div className="text-right">
                <Mono className="block text-muted-foreground">latency</Mono>
                <Mono className="text-base" style={{ color: tone(c.status) }}>
                  {c.latency}ms
                </Mono>
              </div>
            </div>

            <div className="mt-4 h-1 overflow-hidden rounded-full bg-neon/10">
              <motion.div
                className="h-full rounded-full"
                style={{ background: tone(c.status) }}
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(100, c.latency / 12)}%` }}
                transition={{ duration: 1, delay: i * 0.1 }}
              />
            </div>

            <pre className="mt-4 overflow-x-auto rounded-lg border border-neon/15 bg-background/70 p-3 font-mono text-[11px] text-neon/80">
              {c.log}
            </pre>

            <div className="mt-3 flex items-center justify-between">
              <Mono className="text-muted-foreground">
                <Activity className="mr-1 inline size-3" />
                {c.sent} deliveries · 24h
              </Mono>
              <MagneticButton>Reconnect</MagneticButton>
            </div>
          </TerminalCard>
        ))}
      </div>
    </div>
  );
}
