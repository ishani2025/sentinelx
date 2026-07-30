import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useState } from "react";
import { Mono, Panel, PageHeader } from "@/components/soc/primitives";

export const Route = createFileRoute("/policies")({
  head: () => ({
    meta: [
      { title: "Policy Governance · SentinelX SOC" },
      {
        name: "description",
        content:
          "Readable security policies with linked controls, autonomy thresholds and evaluation history for every automated action.",
      },
      { property: "og:title", content: "Policy Governance · SentinelX SOC" },
      {
        property: "og:description",
        content: "Define what the SOC automation may do on its own — and what always needs a human.",
      },
    ],
  }),
  component: GovernancePage,
});

const policies = [
  {
    id: "POL-014",
    name: "Autonomous host isolation",
    controls: ["NIST IR-4", "ISO 27001 A.16", "PCI 12.10"],
    body: `## Intent\nPermit **autonomous isolation** of endpoints when composite risk exceeds 85 and the asset is not a domain controller.\n\n## Conditions\n- risk_score >= 85\n- asset.tier != "dc"\n- change_freeze == false\n\n## Requires approval\n- account.disable\n- data.delete`,
  },
  {
    id: "POL-032",
    name: "Cloud exposure remediation",
    controls: ["CIS AWS 2.1.5", "SOC 2 CC6.6"],
    body: `## Intent\nRevert publicly readable object storage automatically within 5 minutes of detection.\n\n## Conditions\n- provider in ["aws", "gcp", "azure"]\n- resource.public == true`,
  },
  {
    id: "POL-047",
    name: "Identity session hygiene",
    controls: ["NIST IA-5", "ISO 27001 A.9"],
    body: `## Intent\nRevoke refresh tokens on impossible-travel detections for privileged principals.\n\n## Conditions\n- principal.privileged == true\n- signal == "impossible_travel"`,
  },
];

function GovernancePage() {
  const [active, setActive] = useState(policies[0].id);
  const policy = policies.find((p) => p.id === active)!;

  return (
    <div className="mx-auto max-w-[1200px]">
      <PageHeader
        eyebrow="governance/"
        title="Autonomy policies"
        description="Machine-enforced policy is the boundary of AI autonomy. Every stage evaluation cites the policy version it used."
      />
      <div className="grid gap-5 lg:grid-cols-[280px_1fr]">
        <Panel title="Policy set">
          <ul className="p-2">
            {policies.map((p) => (
              <li key={p.id}>
                <button
                  onClick={() => setActive(p.id)}
                  className="relative flex w-full flex-col gap-0.5 rounded-xl px-3 py-2.5 text-left"
                >
                  {active === p.id && (
                    <motion.span
                      layoutId="policy-active"
                      className="absolute inset-0 rounded-xl border border-neon/30 bg-neon/10"
                    />
                  )}
                  <Mono className="relative text-muted-foreground">{p.id}</Mono>
                  <span className="relative text-sm text-foreground/90">{p.name}</span>
                </button>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title={`${policy.id} · ${policy.name}`}>
          <motion.div
            key={policy.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-5"
          >
            <div className="mb-4 flex flex-wrap gap-2">
              {policy.controls.map((c) => (
                <span
                  key={c}
                  className="rounded-lg border border-cyan/30 bg-cyan/10 px-2.5 py-1 font-mono text-[11px] text-cyan"
                >
                  {c}
                </span>
              ))}
            </div>
            <div className="space-y-2">
              {policy.body.split("\n").map((line, i) => {
                if (line.startsWith("## "))
                  return (
                    <h3 key={i} className="pt-2 text-[13px] font-semibold tracking-wide uppercase">
                      {line.slice(3)}
                    </h3>
                  );
                if (line.startsWith("- "))
                  return (
                    <p key={i} className="pl-4 font-mono text-[12px] text-cyan/85">
                      · {line.slice(2)}
                    </p>
                  );
                if (!line.trim()) return null;
                return (
                  <p key={i} className="text-sm text-muted-foreground">
                    {line.replaceAll("**", "")}
                  </p>
                );
              })}
            </div>
          </motion.div>
        </Panel>
      </div>
    </div>
  );
}