import Link from "next/link";

export default function NotFound() {
  return (
    <div className="max-w-lg mx-auto py-20 text-center space-y-4">
      <div className="text-4xl font-black text-indigo-400">404</div>
      <h2 className="text-xl font-bold text-white">Page Not Found</h2>
      <p className="text-sm text-zinc-400">
        The requested resource or ticket could not be found.
      </p>
      <div className="pt-4">
        <Link
          href="/"
          className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
        >
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
}
