"use client";

import React from "react";
import type { TicketDomain, TicketStatus } from "@/lib/api";

export function StatusBadge({ status }: { status: TicketStatus }) {
  const styles: Record<TicketStatus, { bg: string; text: string; dot: string; label: string }> = {
    PENDING: {
      bg: "bg-slate-800 text-slate-300 border-slate-700",
      text: "text-slate-300",
      dot: "bg-slate-400",
      label: "Pending",
    },
    PROCESSING: {
      bg: "bg-blue-950/70 text-blue-300 border-blue-800/60 animate-pulse",
      text: "text-blue-300",
      dot: "bg-blue-400",
      label: "Processing",
    },
    PENDING_REVIEW: {
      bg: "bg-amber-950/70 text-amber-300 border-amber-800/60",
      text: "text-amber-300",
      dot: "bg-amber-400",
      label: "Needs Review",
    },
    RESOLVED: {
      bg: "bg-emerald-950/70 text-emerald-300 border-emerald-800/60",
      text: "text-emerald-300",
      dot: "bg-emerald-400",
      label: "Resolved",
    },
    REJECTED: {
      bg: "bg-rose-950/70 text-rose-300 border-rose-800/60",
      text: "text-rose-300",
      dot: "bg-rose-400",
      label: "Rejected",
    },
    NEEDS_FOLLOW_UP: {
      bg: "bg-purple-950/70 text-purple-300 border-purple-800/60",
      text: "text-purple-300",
      dot: "bg-purple-400",
      label: "Follow-up",
    },
    FAILED: {
      bg: "bg-red-950/70 text-red-300 border-red-800/60",
      text: "text-red-300",
      dot: "bg-red-400",
      label: "Failed",
    },
  };

  const current = styles[status] || styles.PENDING;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${current.bg}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${current.dot}`} />
      {current.label}
    </span>
  );
}

export function DomainBadge({ domain }: { domain?: TicketDomain | null }) {
  if (!domain) return <span className="text-zinc-500 text-xs">—</span>;

  const config: Record<TicketDomain, { label: string; bg: string }> = {
    BILLING: { label: "Billing", bg: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" },
    TECHNICAL_SUPPORT: { label: "Technical", bg: "bg-sky-500/10 text-sky-400 border-sky-500/20" },
    ACCOUNT_MANAGEMENT: { label: "Account", bg: "bg-purple-500/10 text-purple-400 border-purple-500/20" },
    UNKNOWN: { label: "Unknown", bg: "bg-zinc-800 text-zinc-400 border-zinc-700" },
  };

  const curr = config[domain] || config.UNKNOWN;

  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium border ${curr.bg}`}>
      {curr.label}
    </span>
  );
}

export function ConfidenceBadge({ confidence }: { confidence?: number | null }) {
  if (confidence === null || confidence === undefined) {
    return <span className="text-zinc-500 text-xs">—</span>;
  }

  const pct = Math.round(confidence * 100);
  let color = "text-emerald-400";
  if (pct < 65) color = "text-rose-400";
  else if (pct < 80) color = "text-amber-400";

  return (
    <span className={`text-xs font-semibold tabular-nums ${color}`}>
      {pct}%
    </span>
  );
}
