/**
 * CloudDesk Frontend API Client
 */

export type TicketDomain = "BILLING" | "TECHNICAL_SUPPORT" | "ACCOUNT_MANAGEMENT" | "UNKNOWN";

export type TicketStatus =
  | "PENDING"
  | "PROCESSING"
  | "PENDING_REVIEW"
  | "RESOLVED"
  | "REJECTED"
  | "NEEDS_FOLLOW_UP"
  | "FAILED";

export type ReviewDecisionType = "APPROVE" | "EDIT" | "REJECT";

export interface Ticket {
  id: string;
  customer_id?: string | null;
  customer_email: string;
  customer_name?: string | null;
  subject: string;
  body: string;
  domain?: TicketDomain | null;
  confidence?: number | null;
  classification_explanation?: string | null;
  status: TicketStatus;
  workflow_stage?: string | null;
  specialist_results?: string | null;
  draft_reply?: string | null;
  final_reply?: string | null;
  escalation_required: boolean;
  escalation_reason?: string | null;
  error_info?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketListResponse {
  tickets: Ticket[];
  total: number;
  page: number;
  page_size: number;
}

export interface TicketCreateInput {
  customer_email: string;
  customer_name?: string;
  customer_id?: string;
  subject: string;
  body: string;
}

export interface ReviewRequest {
  decision: ReviewDecisionType;
  edited_response?: string;
  rejection_reason?: string;
  reviewer?: string;
}

export interface ReviewResponse {
  ticket_id: string;
  decision: ReviewDecisionType;
  status: TicketStatus;
  reviewer: string;
  final_reply?: string | null;
  rejection_reason?: string | null;
  created_at: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      errorDetail = err.detail || errorDetail;
    } catch {
      // ignore JSON parse fail
    }
    throw new Error(errorDetail);
  }

  return res.json() as Promise<T>;
}

export async function createTicket(input: TicketCreateInput): Promise<Ticket> {
  return fetchJson<Ticket>("/api/tickets", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function listTickets(params?: {
  status?: TicketStatus;
  domain?: TicketDomain;
  page?: number;
  page_size?: number;
}): Promise<TicketListResponse> {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);
  if (params?.domain) query.set("domain", params.domain);
  if (params?.page) query.set("page", params.page.toString());
  if (params?.page_size) query.set("page_size", params.page_size.toString());

  const qs = query.toString() ? `?${query.toString()}` : "";
  return fetchJson<TicketListResponse>(`/api/tickets${qs}`);
}

export async function getTicket(id: string): Promise<Ticket> {
  return fetchJson<Ticket>(`/api/tickets/${id}`);
}

export async function getTicketStatus(id: string): Promise<{
  ticket_id: string;
  status: TicketStatus;
  workflow_stage?: string;
  escalation_required: boolean;
  escalation_reason?: string;
}> {
  return fetchJson(`/api/tickets/${id}/status`);
}

export async function getPendingReviews(): Promise<Ticket[]> {
  return fetchJson<Ticket[]>("/api/reviews/pending");
}

export async function submitReview(
  ticketId: string,
  review: ReviewRequest
): Promise<ReviewResponse> {
  return fetchJson<ReviewResponse>(`/api/tickets/${ticketId}/review`, {
    method: "POST",
    body: JSON.stringify(review),
  });
}
