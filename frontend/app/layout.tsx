import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import ToastProvider from "../components/ToastProvider";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

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
    <html lang="en" suppressHydrationWarning className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900 selection:bg-pink-200 selection:text-pink-900">
        <ToastProvider />
        {children}
      </body>
    </html>
  );
}
