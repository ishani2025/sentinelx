import { motion } from "framer-motion";
import { useState } from "react";
import { graphEdges, graphNodes } from "@/lib/soc-data";

const kindColor: Record<string, string> = {
  identity: "var(--cyan)",
  host: "var(--critical)",
  process: "var(--warning)",
  network: "var(--info)",
  cloud: "var(--neon)",
};

/** correlation/ — entity graph with animated links and risk propagation pulses. */
export function ThreatGraph({ interactive = true }: { interactive?: boolean }) {
  const [hover, setHover] = useState<string | null>(null);
  const at = (id: string) => graphNodes.find((n) => n.id === id)!;

  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="h-full w-full">
      {graphEdges.map(([a, b], i) => {
        const A = at(a);
        const B = at(b);
        const active = hover === a || hover === b;
        return (
          <g key={`${a}-${b}`}>
            <motion.line
              x1={A.x}
              y1={A.y}
              x2={B.x}
              y2={B.y}
              stroke={active ? "var(--neon)" : "var(--border)"}
              strokeWidth={active ? 0.6 : 0.35}
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ pathLength: 1, opacity: 1 }}
              transition={{ duration: 1, delay: i * 0.12 }}
            />
            <motion.circle
              r={0.8}
              fill="var(--neon)"
              initial={{ cx: A.x, cy: A.y, opacity: 0 }}
              animate={{ cx: [A.x, B.x], cy: [A.y, B.y], opacity: [0, 1, 0] }}
              transition={{ duration: 2.6, repeat: Infinity, delay: i * 0.5, ease: "linear" }}
            />
          </g>
        );
      })}
      {graphNodes.map((n, i) => (
        <g
          key={n.id}
          onMouseEnter={() => interactive && setHover(n.id)}
          onMouseLeave={() => interactive && setHover(null)}
        >
          <motion.circle
            cx={n.x}
            cy={n.y}
            r={n.risk > 85 ? 3.4 : 2.6}
            fill={kindColor[n.kind]}
            fillOpacity={hover === n.id ? 1 : 0.85}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 220, damping: 14, delay: i * 0.09 }}
          />
          {n.risk > 85 && (
            <motion.circle
              cx={n.x}
              cy={n.y}
              r={3.4}
              fill="none"
              stroke={kindColor[n.kind]}
              strokeWidth={0.4}
              animate={{ r: [3.4, 8], opacity: [0.7, 0] }}
              transition={{ duration: 2.2, repeat: Infinity, delay: i * 0.3 }}
            />
          )}
          <text
            x={n.x}
            y={n.y - 5}
            textAnchor="middle"
            style={{ fontSize: 2.6, fill: "var(--muted-foreground)", fontFamily: "var(--font-mono)" }}
          >
            {n.label}
          </text>
        </g>
      ))}
    </svg>
  );
}