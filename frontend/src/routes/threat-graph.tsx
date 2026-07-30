import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Mono, Panel, PageHeader } from "@/components/soc/primitives";
import { ThreatGraph } from "@/components/soc/ThreatGraph";
import { graphNodes } from "@/lib/soc-data";

export const Route = createFileRoute("/threat-graph")({
  head: () => ({
    meta: [
      { title: "Correlation Graph · SentinelX SOC" },
      {
        name: "description",
        content:
          "Interactive entity correlation graph with animated links and risk propagation across identity, host, network and cloud planes.",
      },
      { property: "og:title", content: "Correlation Graph · SentinelX SOC" },
      {
        property: "og:description",
        content: "See how alerts cluster into a single intrusion story across every telemetry plane.",
      },
    ],
  }),
  component: CorrelationPage,
});

function CorrelationPage() {
  return (
    <div className="mx-auto max-w-[1400px]">
      <PageHeader
        eyebrow="correlation/"
        title="Cluster CL-118"
        description="Nine edges linking six entities within a 15-minute window. Risk propagates outward from the compromised host."
      />
      <div className="grid gap-5 xl:grid-cols-[1.6fr_1fr]">
        <Panel title="Entity graph" className="scanlines">
          <div className="h-[520px] p-2">
            <ThreatGraph />
          </div>
        </Panel>
        <Panel title="Risk propagation">
          <ul className="divide-y divide-border/50">
            {[...graphNodes]
              .sort((a, b) => b.risk - a.risk)
              .map((n, i) => (
                <li key={n.id} className="px-5 py-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-foreground/90">{n.label}</span>
                    <Mono className="text-muted-foreground">{n.kind}</Mono>
                  </div>
                  <div className="mt-2 flex items-center gap-3">
                    <div className="h-1.5 flex-1 rounded-full bg-elevated">
                      <motion.div
                        className="h-1.5 rounded-full"
                        style={{
                          background: n.risk > 85 ? "var(--critical)" : "var(--gradient-neon)",
                        }}
                        initial={{ width: 0 }}
                        animate={{ width: `${n.risk}%` }}
                        transition={{ duration: 0.9, delay: i * 0.08 }}
                      />
                    </div>
                    <Mono style={{ color: n.risk > 85 ? "var(--critical)" : "var(--neon)" }}>
                      {n.risk}
                    </Mono>
                  </div>
                </li>
              ))}
          </ul>
        </Panel>
      </div>
    </div>
  );
}