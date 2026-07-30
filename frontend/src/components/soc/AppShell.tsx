import { Link, useRouterState } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import {
  Activity,
  ChevronLeft,
  FileBarChart,
  FileLock2,
  Network,
  Plug,
  Radar,
  ScrollText,
  Search,
  Settings2,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { CyberBackground } from "./CyberBackground";
import { Mono } from "./primitives";
import { cn } from "@/lib/utils";

const nav = [
  { to: "/", label: "Dashboard", icon: Radar, hint: "orchestrator/" },
  { to: "/investigations", label: "Investigations", icon: Activity, hint: "agents/" },
  { to: "/threat-graph", label: "Threat Graph", icon: Network, hint: "correlation/" },
  { to: "/playbooks", label: "Playbooks", icon: Workflow, hint: "response/" },
  { to: "/policies", label: "Policies", icon: ScrollText, hint: "docs/" },
  { to: "/evidence", label: "Evidence", icon: FileLock2, hint: "reporting/" },
  { to: "/reports", label: "Reports", icon: FileBarChart, hint: "reporting/" },
  { to: "/integrations", label: "Integrations", icon: Plug, hint: "integrations/" },
  { to: "/settings", label: "Settings", icon: Settings2, hint: "config/" },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
      if (e.key === "Escape") setPaletteOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="relative min-h-dvh">
      <CyberBackground />
      <div className="relative flex min-h-dvh">
        <motion.aside
          animate={{ width: collapsed ? 74 : 248 }}
          transition={{ type: "spring", stiffness: 220, damping: 26 }}
          className="sticky top-0 hidden h-dvh shrink-0 flex-col border-r border-border/80 bg-sidebar/70 backdrop-blur-xl md:flex"
        >
          <div className="flex items-center gap-2.5 px-4 py-5">
            <motion.span
              animate={{ boxShadow: ["0 0 0px var(--neon)", "0 0 18px var(--neon)", "0 0 0px var(--neon)"] }}
              transition={{ duration: 3, repeat: Infinity }}
              className="grid size-9 shrink-0 place-items-center rounded-xl bg-neon/15"
            >
              <ShieldCheck className="size-4.5 text-neon" />
            </motion.span>
            <AnimatePresence initial={false}>
              {!collapsed && (
                <motion.div
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -8 }}
                  className="overflow-hidden whitespace-nowrap"
                >
                  <p className="term text-glow text-[13px] font-bold text-neon">Sentinel X</p>
                  <Mono className="text-neon/50">AI SECURITY OPS CENTER</Mono>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <nav className="flex flex-1 flex-col gap-1 px-3">
            {nav.map((item) => {
              const active = item.to === "/" ? pathname === "/" : pathname.startsWith(item.to);
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  title={item.label}
                  className={cn(
                    "term group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-[10px] font-semibold transition-colors",
                    active
                      ? "text-neon text-glow"
                      : "text-neon/45 hover:bg-neon/5 hover:text-neon",
                  )}
                >
                  {active && (
                    <motion.span
                      layoutId="nav-active"
                      transition={{ type: "spring", stiffness: 320, damping: 30 }}
                      className="absolute inset-0 rounded-xl border border-neon/40 border-l-2 border-l-neon bg-neon/10 shadow-[0_0_24px_-8px_var(--neon)]"
                    />
                  )}
                  <item.icon
                    className={cn(
                      "relative size-4.5 shrink-0 transition-transform group-hover:scale-110",
                      active && "text-neon",
                    )}
                  />
                  <AnimatePresence initial={false}>
                    {!collapsed && (
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="relative truncate"
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </Link>
              );
            })}
          </nav>

          <div className="mx-3 mb-2 rounded-xl border border-neon/20 bg-neon/[0.05] px-3 py-2.5">
            <div className="flex items-center gap-2">
              <motion.span
                className="size-1.5 rounded-full bg-neon"
                animate={{ opacity: [1, 0.25, 1] }}
                transition={{ duration: 1.8, repeat: Infinity }}
              />
              <Mono className="text-neon">SUPERVISOR ONLINE</Mono>
            </div>
            {!collapsed && (
              <Link to="/agents" className="mt-1 block">
                <Mono className="text-neon/45 hover:text-neon">8 AGENTS RUNNING →</Mono>
              </Link>
            )}
          </div>

          <button
            onClick={() => setCollapsed((v) => !v)}
            aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
            className="term m-3 flex items-center justify-center gap-2 rounded-lg border border-neon/20 py-2 text-[10px] text-neon/50 transition-colors hover:border-neon/50 hover:text-neon"
          >
            <motion.span animate={{ rotate: collapsed ? 180 : 0 }}>
              <ChevronLeft className="size-4" />
            </motion.span>
            {!collapsed && "Collapse"}
          </button>
        </motion.aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-border/70 bg-background/70 px-5 py-3 backdrop-blur-xl">
            <button
              onClick={() => setPaletteOpen(true)}
              className="term flex flex-1 items-center gap-2 rounded-xl border border-neon/20 bg-neon/[0.04] px-3 py-2 text-left text-[10px] text-neon/50 transition-colors hover:border-neon/50 hover:text-neon md:max-w-md"
            >
              <Search className="size-3.5" />
              Search incidents · assets · playbooks
              <Mono className="ml-auto rounded border border-border px-1.5 py-0.5">⌘K</Mono>
            </button>
            <div className="ml-auto flex items-center gap-2">
              <span className="flex items-center gap-2 rounded-xl border border-neon/20 bg-neon/[0.04] px-3 py-2">
                <motion.span
                  className="size-2 rounded-full bg-success"
                  animate={{ opacity: [1, 0.3, 1] }}
                  transition={{ duration: 1.6, repeat: Infinity }}
                />
                <Mono className="text-neon/60">INGEST 14.2K EPS</Mono>
              </span>
              <span className="hidden items-center gap-2 rounded-xl border border-critical/40 bg-critical/10 px-3 py-2 shadow-[0_0_24px_-10px_var(--critical)] sm:flex">
                <Mono className="text-critical">1 CRITICAL ACTIVE</Mono>
              </span>
            </div>
          </header>

          <AnimatePresence mode="wait">
            <motion.main
              key={pathname}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
              className="flex-1 px-5 py-6 lg:px-8"
            >
              {children}
            </motion.main>
          </AnimatePresence>
        </div>
      </div>

      <AnimatePresence>
        {paletteOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 grid place-items-start justify-center bg-background/70 pt-[14vh] backdrop-blur-sm"
            onClick={() => setPaletteOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.94, y: -12, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.96, opacity: 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 26 }}
              onClick={(e) => e.stopPropagation()}
              className="glass w-[min(560px,92vw)] rounded-2xl p-2"
            >
              <input
                autoFocus
                aria-label="Command palette"
                placeholder="Jump to module…"
                className="w-full rounded-xl bg-transparent px-3 py-3 text-sm outline-none placeholder:text-muted-foreground"
              />
              <div className="mt-1 border-t border-border/70 pt-2">
                {nav.map((item) => (
                  <Link
                    key={item.to}
                    to={item.to}
                    onClick={() => setPaletteOpen(false)}
                    className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-muted-foreground hover:bg-neon/10 hover:text-foreground"
                  >
                    <item.icon className="size-4" />
                    {item.label}
                    <Mono className="ml-auto text-muted-foreground">{item.hint}</Mono>
                  </Link>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}