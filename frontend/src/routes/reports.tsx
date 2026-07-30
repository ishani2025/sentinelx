import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Bar, BarChart, Cell, ResponsiveContainer, XAxis } from "recharts";
import { MagneticButton, Mono, Panel, PageHeader } from "@/components/soc/primitives";

export const Route = createFileRoute("/reports")({
  head: () => ({
    meta: [
      { title: "Executive Reporting · SentinelX SOC" },
      {
        name: "description",
        content:
          "Board-ready incident reports with animated charts, executive summaries and exportable evidence packs.",
      },
      { property: "og:title", content: "Executive Reporting · SentinelX SOC" },
      {
        property: "og:description",
        content: "Turn a contained incident into a defensible executive narrative in one click.",
      },
    ],
  }),
  component: ReportingPage,
});

const data = [
  { k: "Mon", v: 18 },
  { k: "Tue", v: 26 },
  { k: "Wed", v: 41 },
  { k: "Thu", v: 22 },
  { k: "Fri", v: 33 },
  { k: "Sat", v: 12 },
  { k: "Sun", v: 9 },
];

function ReportingPage() {
  return (
    <div className="mx-auto max-w-[1200px]">
      <PageHeader
        eyebrow="reporting/"
        title="Weekly executive report"
        description="Generated from closed incidents, policy evaluations and response outcomes. Renders to PDF with evidence appendix."
      >
        <MagneticButton variant="neon">Export PDF</MagneticButton>
      </PageHeader>

      <div className="grid gap-5 lg:grid-cols-[1fr_1.2fr]">
        <Panel title="Incidents by day">
          <div className="h-64 px-3 pt-4 pb-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data}>
                <XAxis
                  dataKey="k"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                />
                <Bar dataKey="v" radius={[6, 6, 0, 0]} animationDuration={1100}>
                  {data.map((d) => (
                    <Cell key={d.k} fill={d.v > 35 ? "var(--critical)" : "var(--neon)"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Document preview">
          <motion.article
            initial={{ opacity: 0, y: 16, rotateX: 6 }}
            animate={{ opacity: 1, y: 0, rotateX: 0 }}
            transition={{ duration: 0.6 }}
            className="m-5 rounded-xl border border-border/70 bg-background/70 p-6"
          >
            <Mono className="text-muted-foreground">SENTINELX / CONFIDENTIAL</Mono>
            <h2 className="mt-2 text-lg font-semibold">Security posture summary — week 31</h2>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              161 incidents were triaged, 83% fully automated. One critical credential-access
              intrusion against tier-0 payments infrastructure was contained in 4m 12s with no
              customer impact. Cloud posture improved 6 points after automated bucket remediation.
            </p>
            <ul className="mt-4 space-y-2 text-sm">
              {[
                "Mean time to contain reduced 38% week over week",
                "Credential Access coverage now at 93% of relevant techniques",
                "One policy exception raised: CloudTrail ingest latency above SLO",
              ].map((line, i) => (
                <motion.li
                  key={line}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + i * 0.12 }}
                  className="flex gap-2 text-foreground/85"
                >
                  <span className="text-neon">—</span>
                  {line}
                </motion.li>
              ))}
            </ul>
          </motion.article>
        </Panel>
      </div>
    </div>
  );
}