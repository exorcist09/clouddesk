"use client";

import React, { useEffect } from "react";
import Link from "next/link";

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Application error:", error);
  }, [error]);

  return (
    <div className="max-w-lg mx-auto py-20 text-center space-y-4">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-rose-500/10 text-rose-400 text-2xl font-bold">
        !
      </div>
      <h2 className="text-xl font-bold text-white">Something went wrong</h2>
      <p className="text-sm text-zinc-400">
        {error.message || "An unexpected error occurred while rendering the page."}
      </p>
      <div className="flex items-center justify-center gap-3 pt-4">
        <button
          type="button"
          onClick={() => reset()}
          className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
        >
          Try Again
        </button>
        <Link
          href="/"
          className="px-4 py-2 rounded-lg border border-zinc-800 bg-zinc-900 text-xs text-zinc-300 hover:bg-zinc-800"
        >
          Return Home
        </Link>
      </div>
    </div>
  );
}
