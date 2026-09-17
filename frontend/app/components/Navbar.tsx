"use me";
"use client";

import { useState } from "react";
import { Sparkles, Menu, X, ShieldCheck } from "lucide-react";

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { name: "Home", href: "#hero" },
    { name: "How It Works", href: "#how-it-works" },
    { name: "About", href: "#about" },
  ];

  return (
    <header className="sticky top-0 z-50 glass-nav transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <a
            href="#hero"
            className="flex items-center gap-2.5 group focus:outline-none focus:ring-2 focus:ring-purple-500 rounded-lg p-1"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-pink-500 via-purple-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-pink-500/20 group-hover:scale-105 transition-transform duration-200">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-purple-950 via-purple-900 to-pink-700 bg-clip-text text-transparent">
                Cosmetic<span className="text-pink-600 font-extrabold">Verify</span>
              </span>
              <span className="text-[10px] uppercase tracking-wider font-semibold text-purple-600/80 -mt-1">
                AI Authenticity Platform
              </span>
            </div>
          </a>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 bg-purple-50/60 p-1.5 rounded-full border border-purple-100/80">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                className="px-5 py-2 text-sm font-medium text-purple-950/80 rounded-full hover:text-purple-950 hover:bg-white/90 hover:shadow-xs transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-purple-400"
              >
                {link.name}
              </a>
            ))}
          </nav>

          {/* Action CTA & Mobile Menu Toggle */}
          <div className="flex items-center gap-3">
            <a
              href="#upload-section"
              className="hidden sm:inline-flex items-center justify-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-pink-500 via-purple-600 to-indigo-600 rounded-full shadow-md shadow-pink-500/20 hover:shadow-lg hover:shadow-pink-500/30 hover:opacity-95 active:scale-95 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2"
            >
              <Sparkles className="w-4 h-4 text-pink-200 animate-pulse" />
              <span>Verify Now</span>
            </a>

            {/* Mobile Menu Button */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2.5 rounded-xl text-purple-900 bg-purple-50/80 hover:bg-purple-100 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-colors"
              aria-label="Toggle navigation menu"
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Dropdown Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden glass-card border-t border-purple-100 shadow-xl px-4 pt-3 pb-6 space-y-2">
          {navLinks.map((link) => (
            <a
              key={link.name}
              href={link.href}
              onClick={() => setMobileMenuOpen(false)}
              className="block px-4 py-3 text-base font-semibold text-purple-950 hover:bg-purple-100/60 rounded-xl transition-colors"
            >
              {link.name}
            </a>
          ))}
          <div className="pt-2">
            <a
              href="#upload-section"
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center justify-center gap-2 w-full py-3 text-center text-sm font-semibold text-white bg-gradient-to-r from-pink-500 via-purple-600 to-indigo-600 rounded-xl shadow-md shadow-pink-500/20"
            >
              <Sparkles className="w-4 h-4 text-pink-200" />
              <span>Start Verification</span>
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
