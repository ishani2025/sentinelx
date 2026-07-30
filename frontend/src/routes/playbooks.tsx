import { createFileRoute } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import { MagneticButton, Mono, Panel, PageHeader } from "@/components/soc/primitives";
import { playbooks } from "@/lib/soc-data";

export const Route = createFileRoute("/playbooks")({
  head: () => ({
    meta: [
      { title: "Response Orchestration · SentinelX SOC" },
      {
        name: "description",
        content:
          "Execution timelines, approval workflows and rollback-safe containment playbooks for automated incident response.",
      },
      { property: "og:title", content: "Response Orchestration · SentinelX SOC" },
      {
        property: "og:description",
        content: "Approve, execute and roll back containment actions with full audit visibility.",
      },
    ],
  }),
  component: ResponsePage,
});

const steps = [
  { name: "Isolate host prod-win-app-07", state: "done", ms: 1840 },
  { name: "Revoke active sessions for svc-deploy", state: "done", ms: 920 },
  { name: "Rotate deployment secret", state: "running", ms: 0 },
  { name: "Snapshot disk for forensics", state: "queued", ms: 0 },
];

function ResponsePage() {
  const [approving, setApproving] = useState(false);

  return (
    <div className="mx-auto max-w-[1200px]">
      <PageHeader
        eyebrow="response/"
        title="PB-CRED-01 · Credential access containment"
        description="Four-step playbook with dry-run verification and rollback. One step requires IR lead approval."
      >
        <MagneticButton variant="neon" onClick={() => setApproving(true)}>
          Review approval gate
        </MagneticButton>
      </PageHeader>

      <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr]">
        <Panel title="Execution timeline">
          <ol className="space-y-1 p-5">
            {steps.map((s, i) => (
              <motion.li
                key={s.name}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className="flex items-center gap-3 rounded-xl border border-border/60 bg-background/50 px-4 py-3"
              >
                <span
                  className="size-2.5 rounded-full"
                  style={{
                    background:
                      s.state === "done"
                        ? "var(--success)"
                        : s.state === "running"
                          ? "var(--neon)"
                          : "var(--border)",
                  }}
                />
                <span className="flex-1 text-sm text-foreground/90">{s.name}</span>
                {s.state === "running" && (
                  <div className="h-1 w-24 overflow-hidden rounded-full bg-elevated">
                    <motion.div
                      className="h-1 w-1/3 rounded-full bg-neon"
                      animate={{ x: ["-100%", "300%"] }}
                      transition={{ duration: 1.4, repeat: Infinity, ease: "linear" }}
                    />
                  </div>
                )}
                <Mono className="text-muted-foreground">{s.ms ? `${s.ms}ms` : s.state}</Mono>
              </motion.li>
            ))}
          </ol>
        </Panel>

        <Panel title="Playbook fleet">
          <ul className="divide-y divide-border/50">
            {playbooks.map((pb) => (
              <li key={pb.id} className="px-5 py-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-foreground/90">{pb.name}</span>
                  <Mono className="text-muted-foreground">{pb.state}</Mono>
                </div>
                <div className="mt-2 h-1.5 rounded-full bg-elevated">
                  <motion.div
                    className="h-1.5 rounded-full"
                    style={{
                      background: pb.state === "complete" ? "var(--success)" : "var(--gradient-neon)",
                    }}
                    initial={{ width: 0 }}
                    animate={{ width: `${pb.progress}%` }}
                    transition={{ duration: 1 }}
                  />
                </div>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <AnimatePresence>
        {approving && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setApproving(false)}
            className="fixed inset-0 z-50 grid place-items-center bg-background/70 p-4 backdrop-blur-sm"
          >
            <motion.div
              layout
              initial={{ scale: 0.9, borderRadius: 40, opacity: 0 }}
              animate={{ scale: 1, borderRadius: 20, opacity: 1 }}
              exit={{ scale: 0.92, opacity: 0 }}
              transition={{ type: "spring", stiffness: 260, damping: 24 }}
              onClick={(e) => e.stopPropagation()}
              className="glass w-[min(520px,94vw)] p-6"
            >
              <h2 className="text-base font-semibold">Approve account disable</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                POL-014 permits automatic isolation, but disabling{" "}
                <span className="font-mono text-cyan">svc-deploy</span> impacts 12 downstream
                services and requires IR lead sign-off.
              </p>
              <div className="mt-5 flex justify-end gap-2">
                <MagneticButton onClick={() => setApproving(false)}>Defer</MagneticButton>
                <MagneticButton variant="neon" onClick={() => setApproving(false)}>
                  Approve &amp; execute
                </MagneticButton>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}