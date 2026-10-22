"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import type { Ticket } from "@/lib/api";
import { getPendingReviews } from "@/lib/api";
import { ReviewPanel } from "@/components/review-panel";

export default function ReviewQueuePage() {
  const [pendingTickets, setPendingTickets] = useState<Ticket[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReviews = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const tickets = await getPendingReviews();
      setPendingTickets(tickets);
    } catch (err: any) {
      setError(err?.message || "Failed to load pending reviews");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, []);

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            Admin Review Queue
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Review escalated tickets before automated delivery to customers.
          </p>
        </div>

        <button
          type="button"
          onClick={fetchReviews}
          className="px-3.5 py-2 rounded-lg border border-zinc-800 bg-zinc-900/60 hover:bg-zinc-800 text-xs font-medium text-zinc-300 transition"
        >
          ↻ Refresh Queue
        </button>
      </div>

      {/* Main Review List */}
      {isLoading ? (
        <div className="w-full rounded-2xl border border-zinc-800 bg-zinc-900/40 p-16 text-center">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-amber-500 border-t-transparent" />
          <p className="mt-3 text-sm text-zinc-400">Loading pending reviews...</p>
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl border border-red-800/80 bg-red-950/20 text-red-300 text-sm">
          Failed to fetch review queue: {error}
        </div>
      ) : pendingTickets.length === 0 ? (
        <div className="w-full rounded-2xl border border-zinc-800/80 bg-zinc-950/40 p-16 text-center space-y-3">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-400 text-xl">
            ✓
          </div>
          <h3 className="text-lg font-bold text-zinc-200">Review Queue Empty</h3>
          <p className="text-xs text-zinc-500 max-w-sm mx-auto">
            All tickets have been processed. Escalated tickets requiring human approval will appear here.
          </p>
          <div className="pt-2">
            <Link
              href="/"
              className="px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-xs font-semibold text-zinc-200 transition"
            >
              Return to Dashboard
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="text-xs font-semibold uppercase tracking-wider text-amber-400">
            {pendingTickets.length} Ticket{pendingTickets.length > 1 ? "s" : ""} Requiring Attention
          </div>

          {pendingTickets.map((ticket) => (
            <ReviewPanel
              key={ticket.id}
              ticket={ticket}
              onReviewed={fetchReviews}
            />
          ))}
        </div>
      )}
    </div>
  );
}
