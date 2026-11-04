import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#0B0B12] text-[#F8FAFC]">
      <h2 className="text-2xl font-bold mb-4">404 - Page Not Found</h2>
      <Link href="/" className="px-4 py-2 bg-[#A855F7] hover:bg-[#9333EA] text-white rounded-lg transition-colors">
        Return Home
      </Link>
    </div>
  );
}

