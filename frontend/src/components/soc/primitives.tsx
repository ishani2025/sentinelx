import { motion, type HTMLMotionProps } from "framer-motion";
import { useRef, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Panel({
  className,
  children,
  title,
  action,
  ...rest
}: Omit<HTMLMotionProps<"section">, "title" | "children"> & {
  title?: ReactNode;
  action?: ReactNode;
  children?: ReactNode;
}) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -3 }}
      className={cn("glass relative overflow-hidden rounded-2xl", className)}
      {...rest}
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-neon/50 to-transparent" />
      {(title || action) && (
        <header className="flex items-center justify-between gap-3 border-b border-border/70 px-5 py-3.5">
          <h2 className="term flex items-center gap-2 text-[11px] font-semibold text-neon/90">
            <span className="text-neon/50">/&gt;</span> {title}
          </h2>
          {action}
        </header>
      )}
      {children}
    </motion.section>
  );
}

/** Terminal-style card from the command-center reference: left neon bar + label + value. */
export function TerminalCard({
  label,
  children,
  className,
  delay = 0,
  onClick,
}: {
  label?: string;
  children: ReactNode;
  className?: string;
  delay?: number;
  onClick?: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -14 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] }}
      whileHover={{ y: -3, scale: 1.006 }}
      onClick={onClick}
      className={cn("terminal-card px-4 py-3.5 transition-shadow hover:shadow-[0_0_38px_-6px_var(--neon)]", className)}
    >
      {label && (
        <p className="term text-[10px] text-neon/45">
          <span className="text-neon/35">/&gt;</span> {label}
        </p>
      )}
      <div className="mt-1 font-mono text-sm tracking-wide text-neon">{children}</div>
    </motion.div>
  );
}

/** Outlined neon command button (reference: BENEFITS / GENERAL MAP tiles). */
export function CommandTile({
  icon,
  label,
  onClick,
  delay = 0,
}: {
  icon?: ReactNode;
  label: string;
  onClick?: () => void;
  delay?: number;
}) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      whileHover={{ scale: 1.015 }}
      whileTap={{ scale: 0.985 }}
      className="neon-frame group flex w-full items-center gap-3 px-4 py-3.5 text-left text-neon transition-shadow hover:shadow-[0_0_30px_-6px_var(--neon)]"
    >
      <span className="grid size-6 shrink-0 place-items-center text-neon/80 transition-transform group-hover:scale-110">
        {icon}
      </span>
      <span className="term text-[11px] font-semibold">{label}</span>
    </motion.button>
  );
}

/** Section label: `>>> TEXT <<<` treatment from the reference. */
export function Beacon({ children }: { children: ReactNode }) {
  return (
    <p className="term text-[11px] text-neon/70">
      <span className="text-neon/40">&gt;&gt;&gt;</span> {children}{" "}
      <span className="text-neon/40">&lt;&lt;&lt;</span>
    </p>
  );
}

export function SeverityDot({ color, pulse = false }: { color: string; pulse?: boolean }) {
  return (
    <span className="relative inline-flex size-2.5 shrink-0">
      {pulse && (
        <motion.span
          className="absolute inset-0 rounded-full"
          style={{ background: color }}
          animate={{ scale: [1, 2.4], opacity: [0.6, 0] }}
          transition={{ duration: 1.8, repeat: Infinity, ease: "easeOut" }}
        />
      )}
      <span className="relative size-2.5 rounded-full" style={{ background: color }} />
    </span>
  );
}

export function MagneticButton({
  children,
  className,
  onClick,
  variant = "ghost",
}: {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
  variant?: "ghost" | "neon";
}) {
  const ref = useRef<HTMLButtonElement>(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  return (
    <motion.button
      ref={ref}
      onClick={onClick}
      onMouseMove={(e) => {
        const r = ref.current?.getBoundingClientRect();
        if (!r) return;
        setOffset({
          x: (e.clientX - (r.left + r.width / 2)) * 0.22,
          y: (e.clientY - (r.top + r.height / 2)) * 0.28,
        });
      }}
      onMouseLeave={() => setOffset({ x: 0, y: 0 })}
      animate={{ x: offset.x, y: offset.y }}
      transition={{ type: "spring", stiffness: 260, damping: 18 }}
      whileTap={{ scale: 0.96 }}
      className={cn(
        "term relative inline-flex items-center gap-2 rounded-xl px-3.5 py-2 text-[10px] font-semibold transition-colors",
        variant === "neon"
          ? "neon-frame text-neon hover:bg-neon/15"
          : "border border-neon/25 bg-neon/[0.04] text-neon/70 hover:border-neon/50 hover:text-neon",
        className,
      )}
    >
      {children}
    </motion.button>
  );
}

export function Metric({
  label,
  value,
  delta,
  accent = "var(--neon)",
}: {
  label: string;
  value: string;
  delta?: string;
  accent?: string;
}) {
  return (
    <div className="relative px-5 py-4">
      <p className="term text-[10px] text-neon/45">/&gt; {label}</p>
      <div className="mt-1.5 flex items-baseline gap-2">
        <motion.span
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-glow font-mono text-2xl font-bold tracking-tight"
          style={{ color: accent }}
        >
          {value}
        </motion.span>
        {delta && <span className="font-mono text-[11px] text-muted-foreground">{delta}</span>}
      </div>
    </div>
  );
}

export function Mono({
  children,
  className,
  style,
}: {
  children: ReactNode;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <span style={style} className={cn("font-mono text-[11px] tracking-tight", className)}>
      {children}
    </span>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return (
    <div className={cn("relative overflow-hidden rounded-md bg-elevated/70", className)}>
      <motion.div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(90deg, transparent, color-mix(in oklab, var(--neon) 12%, transparent), transparent)",
        }}
        animate={{ x: ["-100%", "100%"] }}
        transition={{ duration: 1.4, repeat: Infinity, ease: "linear" }}
      />
    </div>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="mb-6 flex flex-wrap items-end justify-between gap-4"
    >
      <div>
        <p className="term text-[10px] text-neon/55">/&gt; {eyebrow}</p>
        <h1 className="text-glow mt-2 font-mono text-2xl font-bold tracking-[0.08em] text-neon uppercase">
          {title}
        </h1>
        <p className="mt-2 max-w-2xl font-mono text-xs tracking-wide text-muted-foreground">
          {description}
        </p>
      </div>
      {children}
    </motion.div>
  );
}