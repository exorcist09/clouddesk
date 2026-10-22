"use client";

import React, { useState } from "react";
import type { ReviewDecisionType, Ticket } from "@/lib/api";
import { submitReview } from "@/lib/api";
import { ConfidenceBadge, DomainBadge } from "@/components/ticket-status";

interface ReviewPanelProps {
  ticket: Ticket;
  onReviewed?: () => void;
}

export function ReviewPanel({ ticket, onReviewed }: ReviewPanelProps) {
  const [mode, setMode] = useState<"view" | "edit" | "reject">("view");
  const [editedText, setEditedText] = useState(ticket.draft_reply || "");
  const [rejectionReason, setRejectionReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDecision = async (decision: ReviewDecisionType) => {
    setIsSubmitting(true);
    setError(null);
    try {
      await submitReview(ticket.id, {
        decision,
        edited_response: decision === "EDIT" ? editedText : undefined,
        rejection_reason: decision === "REJECT" ? rejectionReason : undefined,
        reviewer: "Support Lead",
      });
      if (onReviewed) onReviewed();
    } catch (err: any) {
      setError(err?.message || "Failed to submit review decision");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-6 shadow-2xl backdrop-blur-md space-y-6">
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-800/80 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono text-zinc-500">#{ticket.id.slice(0, 8)}</span>
            <DomainBadge domain={ticket.domain} />
            <ConfidenceBadge confidence={ticket.confidence} />
          </div>
          <h3 className="text-lg font-semibold text-zinc-100 mt-1">{ticket.subject}</h3>
          <p className="text-xs text-zinc-400 mt-0.5">
            From: <span className="text-zinc-200">{ticket.customer_name || ticket.customer_email}</span> ({ticket.customer_email})
          </p>
        </div>
        <div className="px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-medium">
          Pending Human Approval
        </div>
      </div>

      {/* Escalation Alert */}
      {ticket.escalation_reason && (
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4">
          <div className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
            Escalation Trigger
          </div>
          <p className="mt-1 text-sm text-amber-200 font-medium">
            {ticket.escalation_reason}
          </p>
        </div>
      )}

      {/* Original Customer Message */}
      <div className="space-y-1.5">
        <label className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          Customer Inquiry
        </label>
        <div className="rounded-lg border border-zinc-800 bg-zinc-950/70 p-4 text-sm text-zinc-300 whitespace-pre-wrap leading-relaxed">
          {ticket.body}
        </div>
      </div>

      {/* AI Draft Response Section */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-xs font-semibold uppercase tracking-wider text-indigo-400">
            AI Generated Response
          </label>
          {mode === "view" && (
            <button
              type="button"
              onClick={() => setMode("edit")}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium cursor-pointer"
            >
              Edit Draft
            </button>
          )}
        </div>

        {mode === "edit" ? (
          <div className="space-y-3">
            <textarea
              value={editedText}
              onChange={(e) => setEditedText(e.target.value)}
              rows={6}
              className="w-full rounded-lg border border-indigo-500/40 bg-zinc-950 p-4 text-sm text-zinc-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 leading-relaxed font-sans"
              placeholder="Edit response before approving..."
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setMode("view")}
                className="px-3 py-1.5 rounded-lg border border-zinc-700 text-xs font-medium text-zinc-300 hover:bg-zinc-800 cursor-pointer"
              >
                Cancel Edit
              </button>
              <button
                type="button"
                onClick={() => handleDecision("EDIT")}
                disabled={isSubmitting || !editedText.trim()}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition cursor-pointer disabled:opacity-50"
              >
                {isSubmitting ? "Saving..." : "Save & Approve"}
              </button>
            </div>
          </div>
        ) : (
          <div className="rounded-lg border border-indigo-500/20 bg-indigo-950/15 p-4 text-sm text-zinc-200 whitespace-pre-wrap leading-relaxed">
            {ticket.draft_reply || "No draft reply available."}
          </div>
        )}
      </div>

      {/* Rejection Form */}
      {mode === "reject" && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-950/20 p-4 space-y-3">
          <label className="text-xs font-semibold uppercase tracking-wider text-rose-400">
            Rejection Reason
          </label>
          <input
            type="text"
            value={rejectionReason}
            onChange={(e) => setRejectionReason(e.target.value)}
            placeholder="Explain why this ticket draft was rejected..."
            className="w-full rounded-lg border border-rose-500/40 bg-zinc-950 p-3 text-sm text-zinc-200 focus:outline-none focus:ring-2 focus:ring-rose-500"
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setMode("view")}
              className="px-3 py-1.5 rounded-lg border border-zinc-700 text-xs font-medium text-zinc-300 hover:bg-zinc-800 cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => handleDecision("REJECT")}
              disabled={isSubmitting || !rejectionReason.trim()}
              className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold transition cursor-pointer disabled:opacity-50"
            >
              {isSubmitting ? "Rejecting..." : "Confirm Rejection"}
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="p-3 rounded-lg bg-red-950/50 border border-red-800 text-red-300 text-xs">
          {error}
        </div>
      )}

      {/* Action Buttons */}
      {mode === "view" && (
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-zinc-800/80">
          <button
            type="button"
            onClick={() => setMode("reject")}
            disabled={isSubmitting}
            className="px-4 py-2 rounded-lg border border-rose-500/30 text-rose-400 hover:bg-rose-950/40 text-xs font-semibold transition cursor-pointer"
          >
            Reject
          </button>
          <button
            type="button"
            onClick={() => setMode("edit")}
            disabled={isSubmitting}
            className="px-4 py-2 rounded-lg border border-zinc-700 text-zinc-300 hover:bg-zinc-800 text-xs font-semibold transition cursor-pointer"
          >
            Edit & Approve
          </button>
          <button
            type="button"
            onClick={() => handleDecision("APPROVE")}
            disabled={isSubmitting || !ticket.draft_reply}
            className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-900/30 transition cursor-pointer disabled:opacity-50"
          >
            {isSubmitting ? "Approving..." : "Approve Draft"}
          </button>
        </div>
      )}
    </div>
  );
}
