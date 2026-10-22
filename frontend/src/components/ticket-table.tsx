"use client";

import React from "react";
import Link from "next/link";
import type { Ticket } from "@/lib/api";
import { ConfidenceBadge, DomainBadge, StatusBadge } from "@/components/ticket-status";

interface TicketTableProps {
  tickets: Ticket[];
  isLoading?: boolean;
}

export function TicketTable({ tickets, isLoading }: TicketTableProps) {
  if (isLoading) {
    return (
      <div className="w-full rounded-xl border border-zinc-800 bg-zinc-900/40 p-12 text-center">
        <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
        <p className="mt-3 text-sm text-zinc-400">Loading tickets...</p>
      </div>
    );
  }

  if (tickets.length === 0) {
    return (
      <div className="w-full rounded-xl border border-zinc-800 bg-zinc-900/40 p-12 text-center">
        <p className="text-zinc-400 font-medium">No tickets found</p>
        <p className="text-xs text-zinc-500 mt-1">Submit a new ticket or adjust your filters above.</p>
      </div>
    );
  }

  return (
    <div className="w-full overflow-hidden rounded-xl border border-zinc-800/80 bg-zinc-950/60 shadow-xl backdrop-blur-md">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-zinc-300">
          <thead className="bg-zinc-900/60 text-xs font-semibold text-zinc-400 uppercase tracking-wider border-b border-zinc-800/80">
            <tr>
              <th className="px-5 py-3.5">Ticket</th>
              <th className="px-5 py-3.5">Customer</th>
              <th className="px-5 py-3.5">Domain</th>
              <th className="px-5 py-3.5 text-center">Confidence</th>
              <th className="px-5 py-3.5">Status</th>
              <th className="px-5 py-3.5 text-right">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/40 font-normal">
            {tickets.map((t) => (
              <tr
                key={t.id}
                className="hover:bg-zinc-800/30 transition-colors group cursor-pointer"
              >
                <td className="px-5 py-4 font-medium text-zinc-100">
                  <Link href={`/ticket/${t.id}`} className="block">
                    <span className="font-semibold text-zinc-200 group-hover:text-indigo-400 transition-colors line-clamp-1">
                      {t.subject}
                    </span>
                    <span className="text-xs text-zinc-500 font-mono mt-0.5 block">
                      #{t.id.slice(0, 8)}
                    </span>
                  </Link>
                </td>
                <td className="px-5 py-4">
                  <Link href={`/ticket/${t.id}`} className="block">
                    <div className="text-zinc-200 font-medium">{t.customer_name || "—"}</div>
                    <div className="text-xs text-zinc-400 truncate max-w-[200px]">
                      {t.customer_email}
                    </div>
                  </Link>
                </td>
                <td className="px-5 py-4">
                  <DomainBadge domain={t.domain} />
                </td>
                <td className="px-5 py-4 text-center">
                  <ConfidenceBadge confidence={t.confidence} />
                </td>
                <td className="px-5 py-4">
                  <StatusBadge status={t.status} />
                </td>
                <td className="px-5 py-4 text-right text-xs text-zinc-400 whitespace-nowrap">
                  {new Date(t.created_at).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
