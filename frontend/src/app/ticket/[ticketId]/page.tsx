import React, { Suspense } from "react";
import { TicketDetailClient } from "./detail-client";

interface TicketPageProps {
  params: Promise<{ ticketId: string }>;
}

async function TicketLoader({ params }: TicketPageProps) {
  const { ticketId } = await params;
  return <TicketDetailClient ticketId={ticketId} />;
}

export default function TicketDetailPage({ params }: TicketPageProps) {
  return (
    <Suspense
      fallback={
        <div className="max-w-4xl mx-auto py-16 text-center text-sm text-zinc-400">
          <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent mb-2" />
          <p>Loading ticket...</p>
        </div>
      }
    >
      <TicketLoader params={params} />
    </Suspense>
  );
}
