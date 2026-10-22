"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import type { Ticket, TicketDomain, TicketStatus } from "@/lib/api";
import { createTicket, listTickets } from "@/lib/api";
import { TicketTable } from "@/components/ticket-table";

export default function DashboardPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<TicketStatus | "">("");
  const [domainFilter, setDomainFilter] = useState<TicketDomain | "">("");

  // New Ticket Form State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [customerName, setCustomerName] = useState("");
  const [customerEmail, setCustomerEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchTickets = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await listTickets({
        status: statusFilter ? statusFilter : undefined,
        domain: domainFilter ? domainFilter : undefined,
        page_size: 50,
      });
      setTickets(res.tickets);
      setTotal(res.total);
    } catch (err: any) {
      setError(err?.message || "Failed to load tickets");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [statusFilter, domainFilter]);

  const handleCreateTicket = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customerEmail || !subject || !body) return;

    setIsSubmitting(true);
    try {
      await createTicket({
        customer_email: customerEmail,
        customer_name: customerName || undefined,
        subject,
        body,
      });
      setIsModalOpen(false);
      setSubject("");
      setBody("");
      setCustomerEmail("");
      setCustomerName("");
      // Refresh list
      fetchTickets();
    } catch (err: any) {
      alert("Error creating ticket: " + (err?.message || "Unknown error"));
    } finally {
      setIsSubmitting(false);
    }
  };

  const setSampleScenario = (scenario: "billing" | "gantt" | "delete" | "2fa") => {
    if (scenario === "billing") {
      setCustomerName("Priya Sharma");
      setCustomerEmail("priya.sharma@acmecorp.com");
      setSubject("Duplicate charge for ₹2999 on my account");
      setBody("I see two separate ₹2999 transactions for my monthly renewal. Please refund the duplicate.");
    } else if (scenario === "gantt") {
      setCustomerName("Rahul Mehta");
      setCustomerEmail("rahul.mehta@startup.io");
      setSubject("Gantt chart not rendering on Chrome");
      setBody("Whenever I open the Gantt chart in Chrome 124, the entire canvas is blank.");
    } else if (scenario === "delete") {
      setCustomerName("Anjali Patel");
      setCustomerEmail("anjali.patel@freelance.dev");
      setSubject("Delete my account and customer data");
      setBody("I am closing my freelance business. Please permanently delete my account under GDPR.");
    } else if (scenario === "2fa") {
      setCustomerName("Priya Sharma");
      setCustomerEmail("priya.sharma@acmecorp.com");
      setSubject("How do I update my 2FA authentication phone?");
      setBody("I got a new mobile device. How do I transfer my 2FA authenticator?");
    }
  };

  // Quick stats calculations
  const pendingReviewCount = tickets.filter((t) => t.status === "PENDING_REVIEW").length;
  const resolvedCount = tickets.filter((t) => t.status === "RESOLVED").length;
  const processingCount = tickets.filter((t) => t.status === "PROCESSING" || t.status === "PENDING").length;

  return (
    <div className="space-y-8">
      {/* Top Banner / Hero */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Support Operations
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Real-time multi-agent triage, autonomous resolution, and human escalation queue.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={fetchTickets}
            className="px-3.5 py-2 rounded-lg border border-zinc-800 bg-zinc-900/60 hover:bg-zinc-800 text-xs font-medium text-zinc-300 transition"
          >
            ↻ Refresh
          </button>
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition cursor-pointer"
          >
            + New Ticket
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-xl border border-zinc-800/80 bg-zinc-900/40 p-4 backdrop-blur-sm">
          <div className="text-xs font-medium text-zinc-400">Total Tickets</div>
          <div className="text-2xl font-bold text-zinc-100 mt-1 tabular-nums">{total}</div>
        </div>

        <Link
          href="/review"
          className="rounded-xl border border-amber-500/20 bg-amber-500/5 hover:border-amber-500/40 p-4 backdrop-blur-sm transition group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-amber-400">Pending Review</span>
            <span className="text-[10px] uppercase font-bold text-amber-500 group-hover:translate-x-0.5 transition-transform">
              Queue →
            </span>
          </div>
          <div className="text-2xl font-bold text-amber-300 mt-1 tabular-nums">{pendingReviewCount}</div>
        </Link>

        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 backdrop-blur-sm">
          <div className="text-xs font-medium text-emerald-400">Auto-Resolved</div>
          <div className="text-2xl font-bold text-emerald-300 mt-1 tabular-nums">{resolvedCount}</div>
        </div>

        <div className="rounded-xl border border-blue-500/20 bg-blue-500/5 p-4 backdrop-blur-sm">
          <div className="text-xs font-medium text-blue-400">Processing</div>
          <div className="text-2xl font-bold text-blue-300 mt-1 tabular-nums">{processingCount}</div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-zinc-800/80 bg-zinc-900/30 p-3 backdrop-blur-sm">
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider pl-1">
            Filter:
          </span>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as TicketStatus | "")}
            aria-label="Filter by Status"
            className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Statuses</option>
            <option value="PENDING">Pending</option>
            <option value="PROCESSING">Processing</option>
            <option value="PENDING_REVIEW">Needs Review</option>
            <option value="RESOLVED">Resolved</option>
            <option value="REJECTED">Rejected</option>
          </select>

          <select
            value={domainFilter}
            onChange={(e) => setDomainFilter(e.target.value as TicketDomain | "")}
            aria-label="Filter by Domain"
            className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Domains</option>
            <option value="BILLING">Billing</option>
            <option value="TECHNICAL_SUPPORT">Technical Support</option>
            <option value="ACCOUNT_MANAGEMENT">Account Management</option>
            <option value="UNKNOWN">Unknown</option>
          </select>
        </div>

        <div className="text-xs text-zinc-500 font-mono">
          Showing {tickets.length} of {total}
        </div>
      </div>

      {/* Main Ticket Table */}
      {error ? (
        <div className="p-6 rounded-xl border border-red-800/80 bg-red-950/20 text-red-300 text-sm">
          Failed to load tickets: {error}
        </div>
      ) : (
        <TicketTable tickets={tickets} isLoading={isLoading} />
      )}

      {/* New Ticket Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-xl rounded-2xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
              <h2 className="text-lg font-bold text-white">Create Support Ticket</h2>
              <button
                type="button"
                onClick={() => setIsModalOpen(false)}
                className="text-zinc-400 hover:text-white text-lg font-mono"
              >
                ✕
              </button>
            </div>

            {/* Scenario Quick Buttons */}
            <div>
              <div className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider mb-2">
                Sample Test Scenarios:
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setSampleScenario("billing")}
                  className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-[11px] text-zinc-300 border border-zinc-700"
                >
                  ⚡ Duplicate Charge
                </button>
                <button
                  type="button"
                  onClick={() => setSampleScenario("gantt")}
                  className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-[11px] text-zinc-300 border border-zinc-700"
                >
                  ⚡ Gantt Bug
                </button>
                <button
                  type="button"
                  onClick={() => setSampleScenario("delete")}
                  className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-[11px] text-zinc-300 border border-zinc-700"
                >
                  ⚡ Delete Account
                </button>
                <button
                  type="button"
                  onClick={() => setSampleScenario("2fa")}
                  className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-[11px] text-zinc-300 border border-zinc-700"
                >
                  ⚡ Update 2FA
                </button>
              </div>
            </div>

            <form onSubmit={handleCreateTicket} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-zinc-400 block mb-1">Customer Name</label>
                  <input
                    type="text"
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    placeholder="Priya Sharma"
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-zinc-400 block mb-1">
                    Email Address <span className="text-rose-400">*</span>
                  </label>
                  <input
                    type="email"
                    required
                    value={customerEmail}
                    onChange={(e) => setCustomerEmail(e.target.value)}
                    placeholder="customer@example.com"
                    className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-zinc-400 block mb-1">
                  Subject <span className="text-rose-400">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="Summary of issue..."
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-zinc-400 block mb-1">
                  Inquiry Details <span className="text-rose-400">*</span>
                </label>
                <textarea
                  required
                  rows={4}
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  placeholder="Describe your request or issue..."
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 leading-relaxed font-sans"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg border border-zinc-800 text-xs font-medium text-zinc-300 hover:bg-zinc-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition disabled:opacity-50"
                >
                  {isSubmitting ? "Submitting..." : "Submit Ticket"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
