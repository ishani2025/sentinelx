import { motion } from "framer-motion";
import { useMemo } from "react";

/** Ambient SOC backdrop: aurora wash, grid, drifting packets and a slow scan sweep. */
export function CyberBackground() {
  const particles = useMemo(
    () =>
      Array.from({ length: 26 }, (_, i) => ({
        id: i,
        left: (i * 37) % 100,
        top: (i * 61) % 100,
        delay: (i % 9) * 0.9,
        dur: 12 + (i % 7) * 3,
      })),
    [],
  );

  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 overflow-hidden">
      <div className="absolute inset-0" style={{ background: "var(--gradient-aurora)" }} />
      <div
        className="absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage:
            "linear-gradient(to right, color-mix(in oklab, var(--border) 70%, transparent) 1px, transparent 1px), linear-gradient(to bottom, color-mix(in oklab, var(--border) 70%, transparent) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
          maskImage: "radial-gradient(80% 60% at 50% 20%, black, transparent 90%)",
        }}
      />
      {particles.map((p) => (
        <motion.span
          key={p.id}
          className="absolute size-[3px] rounded-full"
          style={{
            left: `${p.left}%`,
            top: `${p.top}%`,
            background: p.id % 3 === 0 ? "var(--cyan)" : "var(--neon)",
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: [0, 0.55, 0], y: [0, -70, -140] }}
          transition={{ duration: p.dur, delay: p.delay, repeat: Infinity, ease: "linear" }}
        />
      ))}
      <motion.div
        className="absolute inset-x-0 h-40"
        style={{
          background:
            "linear-gradient(to bottom, transparent, color-mix(in oklab, var(--neon) 7%, transparent), transparent)",
        }}
        animate={{ y: ["-10%", "110%"] }}
        transition={{ duration: 14, repeat: Infinity, ease: "linear" }}
      />
    </div>
  );
}