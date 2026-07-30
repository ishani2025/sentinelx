import { createFileRoute, Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Metric, Mono, Panel, SeverityDot } from "@/components/soc/primitives";
import { ThreatGraph } from "@/components/soc/ThreatGraph";
import {
  incidents,
  integrations,
  mitreTactics,
  playbooks,
  severityToken,
} from "@/lib/soc-data";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Operations Console · SentinelX SOC" },
      {
        name: "description",
        content:
          "Live incident stream, AI investigation status, MITRE coverage and automation health in a single SOC console.",
      },
      { property: "og:title", content: "Operations Console · SentinelX SOC" },
      {
        property: "og:description",
        content: "Real-time detection, correlation and automated response for enterprise SOC teams.",
      },
    ],
  }),
  component: Operations,
});

const baseSeries = Array.from({ length: 24 }, (_, i) => ({
  t: `${i}:00`,
  events: 400 + Math.round(Math.sin(i / 2.2) * 180 + (i % 5) * 34),
  alerts: 40 + Math.round(Math.cos(i / 3) * 22 + (i % 4) * 6),
}));

function Operations() {
  const [series, setSeries] = useState(baseSeries);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setTick((t) => t + 1);
      setSeries((prev) => {
        const last = prev[prev.length - 1];
        return [
          ...prev.slice(1),
          {
            t: last.t,
            events: 400 + Math.round(Math.random() * 320),
            alerts: 38 + Math.round(Math.random() * 44),
          },
        ];
      });
    }, 3200);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="mx-auto max-w-[1500px] space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="term text-[10px] text-neon/55">/&gt; operations console</p>
          <h1 className="text-glow mt-2 font-mono text-2xl font-bold tracking-[0.08em] text-neon uppercase">
            Active intrusion in <span className="text-critical">payments-vpc</span>
          </h1>
          <p className="mt-2 font-mono text-xs tracking-wide text-muted-foreground">
            Supervisor agent is containing INC-4821. One approval is blocking execution.
          </p>
        </div>
        <Link
          to="/investigations"
          className="term neon-frame px-4 py-2.5 text-[10px] font-semibold text-neon transition-colors hover:bg-neon/15"
        >
          Open live investigation →
        </Link>
      </div>

      <Panel className="grid grid-cols-2 divide-x divide-border/60 lg:grid-cols-5">
        <Metric label="Risk score" value="92" delta="+14 (1h)" accent="var(--critical)" />
        <Metric label="Open incidents" value="27" delta="6 escalated" />
        <Metric label="AI auto-triage" value="83%" delta="of volume" accent="var(--cyan)" />
        <Metric label="Mean time to contain" value="4m 12s" delta="-38% wk" />
        <Metric label="Cloud posture" value="87 / 100" delta="3 drifts" accent="var(--warning)" />
      </Panel>

      <div className="grid gap-5 xl:grid-cols-[1.35fr_1fr]">
        <Panel
          title="Live incident stream"
          action={
            <Mono className="flex items-center gap-2 text-muted-foreground">
              <motion.span
                className="size-1.5 rounded-full bg-neon"
                animate={{ opacity: [1, 0.2, 1] }}
                transition={{ duration: 1.4, repeat: Infinity }}
              />
              streaming
            </Mono>
          }
        >
          <ul className="divide-y divide-border/50">
            {incidents.map((inc, i) => (
              <motion.li
                key={inc.id}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.06 }}
                whileHover={{ backgroundColor: "color-mix(in oklab, var(--neon) 5%, transparent)" }}
                className="flex items-center gap-4 px-5 py-3.5"
              >
                <SeverityDot
                  color={severityToken[inc.severity]}
                  pulse={inc.severity === "critical"}
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <Mono className="text-muted-foreground">{inc.id}</Mono>
                    <p className="truncate text-sm text-foreground/90">{inc.title}</p>
                  </div>
                  <p className="mt-0.5 truncate text-xs text-muted-foreground">
                    {inc.source} · {inc.asset} · {inc.mitre.join(" ")}
                  </p>
                </div>
                <div className="hidden w-32 shrink-0 sm:block">
                  <Mono className="text-muted-foreground">{inc.stage}</Mono>
                  <div className="mt-1.5 h-1 rounded-full bg-elevated">
                    <motion.div
                      className="h-1 rounded-full bg-gradient-to-r from-neon to-cyan"
                      initial={{ width: 0 }}
                      animate={{ width: `${inc.confidence * 100}%` }}
                      transition={{ duration: 0.9, delay: 0.2 + i * 0.05 }}
                    />
                  </div>
                </div>
                <Mono className="w-10 shrink-0 text-right text-muted-foreground">{inc.age}</Mono>
              </motion.li>
            ))}
          </ul>
        </Panel>

        <div className="grid gap-5">
          <Panel title="Telemetry & alert volume">
            <div className="h-52 px-2 pt-4 pb-2">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={series} key={tick}>
                  <defs>
                    <linearGradient id="ev" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--neon)" stopOpacity={0.5} />
                      <stop offset="100%" stopColor="var(--neon)" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="al" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--cyan)" stopOpacity={0.45} />
                      <stop offset="100%" stopColor="var(--cyan)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="t" hide />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{
                      background: "var(--popover)",
                      border: "1px solid var(--border)",
                      borderRadius: 12,
                      fontSize: 12,
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="events"
                    stroke="var(--neon)"
                    fill="url(#ev)"
                    strokeWidth={1.6}
                  />
                  <Area
                    type="monotone"
                    dataKey="alerts"
                    stroke="var(--cyan)"
                    fill="url(#al)"
                    strokeWidth={1.6}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Panel>

          <Panel title="Automation status">
            <ul className="space-y-3 px-5 py-4">
              {playbooks.map((pb, i) => (
                <li key={pb.id}>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-foreground/85">{pb.name}</span>
                    <Mono className="text-muted-foreground">{pb.id}</Mono>
                  </div>
                  <div className="mt-1.5 h-1.5 rounded-full bg-elevated">
                    <motion.div
                      className="h-1.5 rounded-full"
                      style={{
                        background:
                          pb.state === "complete" ? "var(--success)" : "var(--gradient-neon)",
                      }}
                      initial={{ width: 0 }}
                      animate={{ width: `${pb.progress}%` }}
                      transition={{ duration: 1, delay: i * 0.1 }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1fr_1fr_0.8fr]">
        <Panel title="Investigation graph" action={<Mono className="text-muted-foreground">CL-118</Mono>}>
          <div className="h-64">
            <ThreatGraph />
          </div>
        </Panel>

        <Panel title="MITRE ATT&CK coverage">
          <div className="grid grid-cols-1 gap-2 px-5 py-4 sm:grid-cols-2">
            {mitreTactics.map((t, i) => (
              <motion.div
                key={t.name}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.04 }}
                className="rounded-lg border border-border/60 px-3 py-2"
              >
                <div className="flex items-center justify-between">
                  <span className="truncate text-[11px] text-muted-foreground">{t.name}</span>
                  <Mono style={{ color: t.coverage > 75 ? "var(--neon)" : "var(--warning)" }}>
                    {t.coverage}%
                  </Mono>
                </div>
                <div className="mt-1.5 h-1 rounded-full bg-elevated">
                  <motion.div
                    className="h-1 rounded-full"
                    style={{
                      background: t.coverage > 75 ? "var(--neon)" : "var(--warning)",
                    }}
                    initial={{ width: 0 }}
                    animate={{ width: `${t.coverage}%` }}
                    transition={{ duration: 0.8, delay: 0.1 + i * 0.03 }}
                  />
                </div>
              </motion.div>
            ))}
          </div>
        </Panel>

        <Panel title="Integration health">
          <ul className="divide-y divide-border/50">
            {integrations.map((int) => (
              <li key={int.name} className="flex items-center gap-3 px-5 py-3">
                <SeverityDot
                  color={int.status === "healthy" ? "var(--success)" : "var(--warning)"}
                  pulse={int.status !== "healthy"}
                />
                <span className="flex-1 truncate text-xs text-foreground/85">{int.name}</span>
                <Mono className="text-muted-foreground">{int.latency}</Mono>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </div>
  );
}
