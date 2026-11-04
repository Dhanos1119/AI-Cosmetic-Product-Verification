import type { Metadata } from "next";
import "./globals.css";
import ToastProvider from "../components/ToastProvider";

export const metadata: Metadata = {
  title: "CosmeticVerify | AI Cosmetic Product Verification & Marketplace Trust",
  description: "Upload a cosmetic product image and discover product details, review trust, and reliable marketplace recommendations.",
  keywords: ["Cosmetics Verification", "Beauty AI", "Product Trust", "Marketplace Recommendation", "CosmeticVerify"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="h-full antialiased dark">
      <body className="min-h-full flex flex-col bg-[#0B0B12] text-[#F8FAFC] selection:bg-[#EC4899]/30 selection:text-[#F8FAFC]">
        <ToastProvider />
        {children}
      </body>
    </html>
  );
}
