"use client";

import { useState, useEffect } from "react";
import { ShieldCheck } from "lucide-react";

export default function Footer() {
  const [year, setYear] = useState<number | null>(null);

  useEffect(() => {
    setYear(new Date().getFullYear());
  }, []);

  return (
    <footer className="bg-[#0B0B12] text-[#A1A1B5] border-t border-[#303047] pt-12 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 pb-10 border-b border-[#303047]">
          {/* Brand Column */}
          <div className="md:col-span-6 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#EC4899] via-[#A855F7] to-[#8B5CF6] flex items-center justify-center text-white shadow-md shadow-purple-950/40">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <span className="text-xl font-bold tracking-tight text-[#F8FAFC]">
                Cosmetic<span className="text-[#EC4899]">Verify</span>
              </span>
            </div>
            <p className="text-sm text-[#A1A1B5] max-w-sm leading-relaxed">
              AI Cosmetic Product Verification and Trustworthy Marketplace Recommendation System.
            </p>
            <div className="inline-block px-3 py-1 rounded-md bg-[#202033] border border-[#303047] text-[#A855F7] text-xs font-semibold">
              Independent AI Product Verification Platform
            </div>
          </div>

          {/* Navigation Quick Links */}
          <div className="md:col-span-3 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#F8FAFC]">
              Quick Links
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#hero" className="hover:text-[#EC4899] transition-colors">
                  Home
                </a>
              </li>
              <li>
                <a href="#verification-workspace" className="hover:text-[#EC4899] transition-colors">
                  Start Verification
                </a>
              </li>
              <li>
                <a href="#features" className="hover:text-[#EC4899] transition-colors">
                  System Capabilities
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-[#EC4899] transition-colors">
                  How It Works
                </a>
              </li>
              <li>
                <a href="#about" className="hover:text-[#EC4899] transition-colors">
                  About Project
                </a>
              </li>
            </ul>
          </div>

          {/* System Notice */}
          <div className="md:col-span-3 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#F8FAFC]">
              Architecture Status
            </h4>
            <p className="text-xs text-[#A1A1B5] leading-relaxed">
              AI-driven cosmetic product image analysis, CLIP embedding match, OCR text extraction, multi-marketplace cross-referencing, and review credibility evaluation.
            </p>
          </div>
        </div>

        {/* Bottom Copyright Bar */}
        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#A1A1B5]">
          <p suppressHydrationWarning>
            © {year ?? new Date().getFullYear()} CosmeticVerify. All rights reserved.
          </p>
          <div className="flex items-center gap-1">
            <span>AI Cosmetic Product Verification System</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
