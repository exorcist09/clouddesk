import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"], 
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CloudDesk",
  description: "Autonomous multi-agent customer support with LangGraph RAG and human-in-the-loop review.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full dark`}
    >
      <body className="min-h-full flex flex-col bg-zinc-950 text-zinc-100 antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
        {/* Top Navbar */}
        <header className="sticky top-0 z-50 border-b border-zinc-800 bg-zinc-950/95 backdrop-blur-md">
          <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-8">
              <Link href="/" className="flex items-center gap-2.5 group">
                <div>
                  <span className="font-bold text-base tracking-tight text-zinc-100 group-hover:text-indigo-300 transition-colors">
                    CloudDesk
                  </span>
                  <span className="ml-1.5 rounded-full bg-indigo-500/10 px-2 py-0.5 text-[10px] font-semibold text-indigo-400 border border-indigo-500/20">
                    Agent
                  </span>
                </div>
              </Link>

              <nav className="hidden md:flex items-center gap-1">
                <Link
                  href="/"
                  className="rounded-lg px-3 py-2 text-sm font-medium text-zinc-300 hover:text-white hover:bg-zinc-800/50 transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  href="/review"
                  className="rounded-lg px-3 py-2 text-sm font-medium text-zinc-300 hover:text-white hover:bg-zinc-800/50 transition-colors"
                >
                  Admin Review Queue
                </Link>
              </nav>
            </div>

            <div className="flex items-center gap-3">
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noreferrer"
                className="hidden sm:inline-flex items-center rounded-lg border border-zinc-800 bg-zinc-900/50 px-3 py-1.5 text-xs font-medium text-zinc-400 hover:text-zinc-200 hover:border-zinc-700 transition"
              >
                API Docs ↗
              </a>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          {children}
        </main>

      </body>
    </html>
  );
}
