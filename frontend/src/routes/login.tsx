import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Fingerprint, KeyRound, Loader2, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { CyberBackground } from "@/components/soc/CyberBackground";
import { AgentChain } from "@/components/soc/AgentChain";
import { Beacon, CommandTile } from "@/components/soc/primitives";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Authenticate · SentinelX AI SOC" },
      {
        name: "description",
        content:
          "Authenticate into the SentinelX AI Security Operations Center with AWS IAM, Okta, Azure AD or Google.",
      },
      { property: "og:title", content: "Authenticate · SentinelX AI SOC" },
      {
        property: "og:description",
        content: "Secure access to the SentinelX autonomous SOC command center.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Login,
});

const providers = ["AWS IAM", "Okta", "Azure AD", "Google"];

const systems = [
  "GuardDuty connected",
  "CloudTrail streaming",
  "Security Hub active",
  "Macie healthy",
];

function Login() {
  const navigate = useNavigate();
  const [pending, setPending] = useState<string | null>(null);

  const authenticate = (p: string) => {
    setPending(p);
    setTimeout(() => navigate({ to: "/" }), 1100);
  };

  return (
    <div className="relative grid min-h-dvh grid-cols-1 lg:grid-cols-2">
      <CyberBackground />

      <section className="relative hidden items-center justify-center border-r border-neon/15 p-10 lg:flex">
        <AgentChain />
      </section>

      <section className="relative flex items-center justify-center px-6 py-14">
        <div className="w-full max-w-md">
          <motion.div
            initial={{ opacity: 0, y: -14 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <p className="term text-sm text-neon/70">Welcome back,</p>
            <h1 className="text-glow font-mono text-4xl font-black tracking-[0.12em] text-neon uppercase">
              Commander!
            </h1>
            <div className="mt-4 flex justify-center">
              <Beacon>Authenticate to continue your mission</Beacon>
            </div>
          </motion.div>

          <div className="my-8 flex items-center gap-3">
            <span className="h-px flex-1 bg-gradient-to-r from-transparent to-neon/30" />
            <span className="term text-[10px] text-neon/50">or</span>
            <span className="h-px flex-1 bg-gradient-to-l from-transparent to-neon/30" />
          </div>

          <div className="space-y-3">
            {providers.map((p, i) => (
              <CommandTile
                key={p}
                delay={0.1 + i * 0.08}
                icon={i === 0 ? <ShieldCheck className="size-4" /> : i === 1 ? <KeyRound className="size-4" /> : <Fingerprint className="size-4" />}
                label={pending === p ? "authenticating…" : `Continue with ${p}`}
                onClick={() => authenticate(p)}
              />
            ))}
          </div>

          <AnimatePresence>
            {pending && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="term mt-4 flex items-center justify-center gap-2 text-[10px] text-neon"
              >
                <Loader2 className="size-3 animate-spin" /> establishing session · {pending}
              </motion.p>
            )}
          </AnimatePresence>

          <ul className="mt-10 space-y-2">
            {systems.map((s, i) => (
              <motion.li
                key={s}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + i * 0.15 }}
                className="term flex items-center gap-2 text-[10px] text-neon/60"
              >
                <Check className="size-3 text-neon" />
                {s}
                <motion.span
                  className="ml-auto size-1.5 rounded-full bg-neon"
                  animate={{ opacity: [1, 0.2, 1] }}
                  transition={{ duration: 2, repeat: Infinity, delay: i * 0.3 }}
                />
              </motion.li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
