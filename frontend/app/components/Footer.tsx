"use client";

import { ShieldCheck, Heart } from "lucide-react";

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-slate-950 text-slate-300 border-t border-slate-900 pt-12 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 pb-10 border-b border-slate-900">
          {/* Brand Col */}
          <div className="md:col-span-6 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-pink-500 via-purple-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-pink-500/20">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <span className="text-xl font-bold tracking-tight text-white">
                Cosmetic<span className="text-pink-400">Verify</span>
              </span>
            </div>
            <p className="text-sm text-slate-400 max-w-sm leading-relaxed">
              AI Cosmetic Product Verification and Trustworthy Marketplace Recommendation System.
            </p>
            <div className="inline-block px-3 py-1 rounded-md bg-purple-950/80 border border-purple-800/60 text-purple-300 text-xs font-semibold">
              Semester 6 Data Management Project
            </div>
          </div>

          {/* Quick Navigation Links */}
          <div className="md:col-span-3 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Quick Links
            </h4>
            <ul className="space-y-2 text-sm">
              <li>
                <a href="#hero" className="hover:text-pink-400 transition-colors">
                  Home
                </a>
              </li>
              <li>
                <a href="#upload-section" className="hover:text-pink-400 transition-colors">
                  Start Verification
                </a>
              </li>
              <li>
                <a href="#features" className="hover:text-pink-400 transition-colors">
                  Capabilities
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-pink-400 transition-colors">
                  How It Works
                </a>
              </li>
              <li>
                <a href="#about" className="hover:text-pink-400 transition-colors">
                  About Project
                </a>
              </li>
            </ul>
          </div>

          {/* Project Details */}
          <div className="md:col-span-3 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              System Scope
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Frontend prototype interface demonstrating cosmetic product image upload, authenticity validation concepts, and marketplace trust metrics.
            </p>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
          <p>© {currentYear} CosmeticVerify. All rights reserved.</p>
          <div className="flex items-center gap-1">
            <span>Built for Semester 6 Data Management</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
