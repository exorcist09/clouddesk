"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import type { Ticket } from "@/lib/api";
import { getTicket } from "@/lib/api";
import { ConfidenceBadge, DomainBadge, StatusBadge } from "@/components/ticket-status";
import { ReviewPanel } from "@/components/review-panel";

export function TicketDetailClient({ ticketId }: { ticketId: string }) {
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTicket = async () => {
    if (!ticketId) return;
    try {
      const data = await getTicket(ticketId);
      setTicket(data);
    } catch (err: any) {
      setError(err?.message || "Failed to load ticket details");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTicket();

    // Auto-poll while ticket is running in background
    const interval = setInterval(() => {
      if (ticket?.status === "PENDING" || ticket?.status === "PROCESSING") {
        fetchTicket();
      }
    }, 2500);

    return () => clearInterval(interval);
  }, [ticketId, ticket?.status]);

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center">
        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
        <p className="mt-3 text-sm text-zinc-400">Loading ticket details...</p>
      </div>
    );
  }

  if (error || !ticket) {
    return (
      <div className="max-w-4xl mx-auto py-12">
        <div className="rounded-xl border border-red-800 bg-red-950/20 p-6 text-center space-y-3">
          <p className="text-red-300 font-semibold">{error || "Ticket not found"}</p>
          <Link
            href="/"
            className="inline-block px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs text-zinc-200"
          >
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Breadcrumb & Actions */}
      <div className="flex items-center justify-between">
        <Link
          href="/"
          className="text-xs font-medium text-zinc-400 hover:text-white transition"
        >
          ← Back to Dashboard
        </Link>
        <button
          type="button"
          onClick={fetchTicket}
          className="text-xs text-zinc-400 hover:text-zinc-200 cursor-pointer"
        >
          ↻ Refresh Status
        </button>
      </div>

      {/* Ticket Header Card */}
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800/80 pb-4">
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-mono text-zinc-500">#{ticket.id}</span>
            <StatusBadge status={ticket.status} />
          </div>
          <div className="text-xs text-zinc-400">
            Created: {new Date(ticket.created_at).toLocaleString()}
          </div>
        </div>

        <h1 className="text-xl sm:text-2xl font-bold text-white leading-tight">
          {ticket.subject}
        </h1>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1 text-xs">
          <div className="rounded-lg bg-zinc-950/60 p-3 border border-zinc-800/60">
            <span className="text-zinc-500 block">Customer</span>
            <span className="text-zinc-200 font-medium block mt-0.5">
              {ticket.customer_name || "—"}
            </span>
            <span className="text-zinc-400 font-mono text-[11px] block truncate">
              {ticket.customer_email}
            </span>
          </div>

          <div className="rounded-lg bg-zinc-950/60 p-3 border border-zinc-800/60">
            <span className="text-zinc-500 block">Classification</span>
            <div className="mt-1 flex items-center gap-2">
              <DomainBadge domain={ticket.domain} />
              <ConfidenceBadge confidence={ticket.confidence} />
            </div>
          </div>

          <div className="rounded-lg bg-zinc-950/60 p-3 border border-zinc-800/60">
            <span className="text-zinc-500 block">Workflow Stage</span>
            <span className="text-zinc-200 font-mono block mt-0.5 font-medium">
              {ticket.workflow_stage || ticket.status}
            </span>
          </div>
        </div>
      </div>

      {/* Escalation Warning */}
      {ticket.escalation_required && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-5 space-y-1">
          <div className="text-xs font-bold text-amber-400 uppercase tracking-wider">
            Escalation Rule Triggered
          </div>
          <p className="text-sm text-amber-200 font-medium">
            {ticket.escalation_reason || "Escalated for human oversight."}
          </p>
        </div>
      )}

      {/* Customer Inquiry Body */}
      <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 space-y-2">
        <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">
          Customer Inquiry
        </h3>
        <div className="rounded-xl border border-zinc-800/80 bg-zinc-950/80 p-5 text-sm text-zinc-200 whitespace-pre-wrap leading-relaxed font-sans">
          {ticket.body}
        </div>
      </div>

      {/* AI Draft vs Final Reply */}
      {ticket.final_reply ? (
        <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/15 p-6 space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
              Final Resolved Reply Sent to Customer
            </h3>
            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-300">
              Resolved
            </span>
          </div>
          <div className="rounded-xl border border-emerald-500/20 bg-zinc-950/90 p-5 text-sm text-zinc-200 whitespace-pre-wrap leading-relaxed">
            {ticket.final_reply}
          </div>
        </div>
      ) : ticket.draft_reply ? (
        <div className="rounded-2xl border border-indigo-500/30 bg-indigo-950/15 p-6 space-y-2">
          <h3 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
            AI Generated Draft
          </h3>
          <div className="rounded-xl border border-indigo-500/20 bg-zinc-950/90 p-5 text-sm text-zinc-200 whitespace-pre-wrap leading-relaxed">
            {ticket.draft_reply}
          </div>
        </div>
      ) : null}

      {/* Error Info if Failed */}
      {ticket.error_info && (
        <div className="rounded-xl border border-red-500/30 bg-red-950/20 p-4">
          <span className="text-xs font-semibold text-red-400 uppercase block">Error Info</span>
          <p className="text-xs text-red-200 mt-1 font-mono">{ticket.error_info}</p>
        </div>
      )}

      {/* Manager Review Action Panel if ticket is PENDING_REVIEW */}
      {ticket.status === "PENDING_REVIEW" && (
        <div className="pt-2">
          <ReviewPanel ticket={ticket} onReviewed={fetchTicket} />
        </div>
      )}
    </div>
  );
}
