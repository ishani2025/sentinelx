import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { Download, FileLock2 } from "lucide-react";
import { useState } from "react";
import { MagneticButton, Mono, PageHeader, TerminalCard } from "@/components/soc/primitives";

export const Route = createFileRoute("/evidence")({
  head: () => ({
    meta: [
      { title: "Evidence Vault · SentinelX SOC" },
      {
        name: "description",
        content:
          "Immutable, hash-chained evidence artifacts collected by SentinelX agents during automated investigations.",
      },
      { property: "og:title", content: "Evidence Vault · SentinelX SOC" },
      {
        property: "og:description",
        content: "Chain-of-custody artifacts, hashes and retention state for every SOC investigation.",
      },
    ],
  }),
  component: Evidence,
});

const artifacts = [
  { id: "EV-9921", kind: "memory dump", case: "INC-4821", size: "1.4 GB", sha: "9f21ac…c40b", agent: "host-forensics", at: "12:04:19Z" },
  { id: "EV-9920", kind: "process tree", case: "INC-4821", size: "24 KB", sha: "1ab902…7fe1", agent: "host-forensics", at: "12:04:02Z" },
  { id: "EV-9918", kind: "identity sign-in log", case: "INC-4818", size: "812 KB", sha: "77cd41…9012", agent: "identity", at: "11:58:47Z" },
  { id: "EV-9915", kind: "cloudtrail slice", case: "INC-4814", size: "3.1 MB", sha: "0cc7de…aa38", agent: "cloud", at: "11:41:20Z" },
  { id: "EV-9911", kind: "pcap window", case: "INC-4809", size: "48 MB", sha: "b41e00…d5c9", agent: "network", at: "11:22:03Z" },
];

function Evidence() {
  const [selected, setSelected] = useState(artifacts[0].id);
  const active = artifacts.find((a) => a.id === selected)!;

  return (
    <div className="mx-auto max-w-[1300px]">
      <PageHeader
        eyebrow="reporting/evidence"
        title="Evidence vault"
        description="Write-once artifacts with a verifiable hash chain. Every agent collection step is signed and retained for 400 days."
      >
        <MagneticButton variant="neon">
          <Download className="size-3.5" /> Export package
        </MagneticButton>
      </PageHeader>

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-3">
          {artifacts.map((a, i) => (
            <TerminalCard
              key={a.id}
              delay={i * 0.06}
              onClick={() => setSelected(a.id)}
              className={`cursor-pointer ${a.id === selected ? "shadow-[0_0_34px_-6px_var(--neon)]" : "opacity-80"}`}
            >
              <div className="flex flex-wrap items-center gap-3">
                <FileLock2 className="size-4 text-neon/70" />
                <span className="term text-[11px] font-semibold">{a.id}</span>
                <span className="font-mono text-xs text-muted-foreground">{a.kind}</span>
                <Mono className="ml-auto text-neon/70">{a.case}</Mono>
                <Mono className="text-muted-foreground">{a.size}</Mono>
              </div>
            </TerminalCard>
          ))}
        </div>

        <motion.aside
          key={active.id}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="terminal-card h-fit px-5 py-4"
        >
          <p className="term text-[10px] text-neon/50">/&gt; chain of custody</p>
          <h2 className="text-glow mt-2 font-mono text-xl font-bold tracking-widest uppercase">
            {active.id}
          </h2>
          <dl className="mt-4 space-y-2 font-mono text-[11px]">
            {[
              ["artifact", active.kind],
              ["case", active.case],
              ["collected_by", `agents/${active.agent}`],
              ["collected_at", active.at],
              ["sha256", active.sha],
              ["retention", "400d · WORM"],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between gap-4 border-b border-neon/10 pb-1.5">
                <dt className="text-muted-foreground">{k}</dt>
                <dd className="text-neon">{v}</dd>
              </div>
            ))}
          </dl>
          <div className="mt-4 flex gap-2">
            <MagneticButton>Verify hash</MagneticButton>
            <MagneticButton variant="neon">Download</MagneticButton>
          </div>
        </motion.aside>
      </div>
    </div>
  );
}
