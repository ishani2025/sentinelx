import { motion } from "framer-motion";

const chain = [
  "Supervisor",
  "Business Context",
  "Historical",
  "Risk",
  "Policy",
  "Planning",
  "Verification",
  "Execution",
];

/** agents/ — vertical agent mesh with glowing nodes and travelling packets. */
export function AgentChain() {
  return (
    <div className="relative w-full max-w-sm">
      <p className="term mb-6 text-[10px] text-neon/50">/&gt; agent mesh · 8 nodes online</p>
      <div className="relative space-y-3">
        <div className="absolute top-3 bottom-3 left-[13px] w-px bg-neon/20" />
        <motion.span
          className="absolute left-[10px] size-1.5 rounded-full bg-neon shadow-[0_0_12px_var(--neon)]"
          animate={{ top: ["2%", "96%"] }}
          transition={{ duration: 4.5, repeat: Infinity, ease: "linear" }}
        />
        {chain.map((node, i) => (
          <motion.div
            key={node}
            initial={{ opacity: 0, x: -16 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.12, duration: 0.5 }}
            className="relative flex items-center gap-4"
          >
            <motion.span
              className="grid size-7 shrink-0 place-items-center rounded-full border border-neon/40 bg-neon/10"
              animate={{ boxShadow: ["0 0 0px var(--neon)", "0 0 16px var(--neon)", "0 0 0px var(--neon)"] }}
              transition={{ duration: 2.8, repeat: Infinity, delay: i * 0.25 }}
            >
              <span className="size-1.5 rounded-full bg-neon" />
            </motion.span>
            <span className="terminal-card flex-1 px-3 py-2 font-mono text-[11px] tracking-widest text-neon uppercase">
              {node}
            </span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
