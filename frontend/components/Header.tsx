"use client";

import { useState, useEffect } from "react";
import { ShieldCheck, Sparkles, Menu, X, LogIn, LogOut, User, UserPlus, CheckCircle2 } from "lucide-react";

interface HeaderProps {
  user: { email: string; name: string } | null;
  onOpenLogin: () => void;
  onOpenSignup: () => void;
  onLogout: () => void;
  onNavigateToWorkspace: () => void;
}

export default function Header({
  user,
  onOpenLogin,
  onOpenSignup,
  onLogout,
  onNavigateToWorkspace,
}: HeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { name: "Home", href: "#hero" },
    { name: "How It Works", href: "#how-it-works" },
    { name: "About", href: "#about" },
    ...(user ? [{ name: "Workspace", href: "#verification-workspace" }] : []),
  ];

  const handleNavClick = (href: string) => {
    setMobileMenuOpen(false);
    const element = document.querySelector(href);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    }
  };

  // Close mobile menu on resize to desktop
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768) {
        setMobileMenuOpen(false);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <header className="sticky top-0 z-40 glass-nav transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Brand Logo */}
          <a
            href="#hero"
            onClick={(e) => {
              e.preventDefault();
              handleNavClick("#hero");
            }}
            className="flex items-center gap-2.5 group focus:outline-none focus:ring-2 focus:ring-purple-500 rounded-xl p-1 touch-manipulation cursor-pointer"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-pink-500 via-purple-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-pink-500/20 group-hover:scale-105 transition-transform duration-200">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-purple-950 via-purple-900 to-pink-700 bg-clip-text text-transparent">
                Cosmetic<span className="text-pink-600 font-extrabold">Verify</span>
              </span>
              <span className="text-[10px] uppercase tracking-wider font-semibold text-purple-600/80 -mt-1">
                AI Authenticity System
              </span>
            </div>
          </a>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-1 bg-purple-50/70 p-1.5 rounded-full border border-purple-100/90">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                onClick={(e) => {
                  e.preventDefault();
                  handleNavClick(link.href);
                }}
                className="px-4 py-2 text-xs sm:text-sm font-medium text-purple-950/80 rounded-full hover:text-purple-950 hover:bg-white hover:shadow-xs transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-purple-400 touch-manipulation cursor-pointer"
              >
                {link.name}
              </a>
            ))}
          </nav>

          {/* User Auth Action Controls */}
          <div className="flex items-center gap-3">
            {!user ? (
              /* LOGGED-OUT STATE BUTTONS (Desktop) */
              <div className="hidden sm:flex items-center gap-2.5">
                <button
                  type="button"
                  onClick={onOpenLogin}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-purple-950 bg-white hover:bg-purple-50 border border-purple-200 rounded-full shadow-2xs transition-all touch-manipulation min-h-[40px] cursor-pointer focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <LogIn className="w-3.5 h-3.5 text-purple-600" />
                  <span>Login</span>
                </button>

                <button
                  type="button"
                  onClick={onOpenSignup}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-gradient-to-r from-pink-500 via-purple-600 to-indigo-600 rounded-full shadow-md hover:opacity-95 transition-all touch-manipulation min-h-[40px] cursor-pointer focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>Sign Up</span>
                </button>
              </div>
            ) : (
              /* LOGGED-IN STATE CONTROLS (Desktop) */
              <div className="flex items-center gap-3">
                <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 bg-purple-100/90 border border-purple-200/90 rounded-full text-xs font-semibold text-purple-950 shadow-2xs">
                  <div className="w-5 h-5 rounded-full bg-purple-600 text-white flex items-center justify-center text-[10px] font-bold">
                    {user.name ? user.name[0].toUpperCase() : "D"}
                  </div>
                  <span className="max-w-[110px] truncate">{user.email}</span>
                  <span className="text-[10px] uppercase font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full border border-emerald-200 flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    <span>Signed in</span>
                  </span>
                </div>

                <button
                  type="button"
                  onClick={onLogout}
                  className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-full transition-colors touch-manipulation min-h-[38px] cursor-pointer focus:outline-none focus:ring-2 focus:ring-rose-400"
                  title="Sign out of demo account"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            )}

            {/* Workspace CTA Button */}
            <button
              type="button"
              onClick={onNavigateToWorkspace}
              className="hidden sm:inline-flex items-center justify-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-purple-950 hover:bg-purple-900 rounded-full shadow-md transition-all touch-manipulation min-h-[40px] cursor-pointer focus:outline-none focus:ring-2 focus:ring-purple-500"
            >
              <Sparkles className="w-3.5 h-3.5 text-pink-300 animate-pulse" />
              <span>{user ? "Go to Workspace" : "Verification"}</span>
            </button>

            {/* Mobile Hamburger Toggle Button */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2.5 rounded-xl text-purple-950 bg-purple-100/80 hover:bg-purple-200 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-colors touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer relative z-50"
              aria-label="Toggle navigation menu"
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Dropdown Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden relative z-45 glass-card border-t border-purple-100 shadow-xl px-4 pt-3 pb-6 space-y-3 animate-fadeIn">
          {navLinks.map((link) => (
            <a
              key={link.name}
              href={link.href}
              onClick={(e) => {
                e.preventDefault();
                handleNavClick(link.href);
              }}
              className="block px-4 py-3 text-base font-semibold text-purple-950 hover:bg-purple-100/70 active:bg-purple-200/80 rounded-xl transition-colors touch-manipulation min-h-[44px] cursor-pointer"
            >
              {link.name}
            </a>
          ))}

          {/* User state in mobile dropdown */}
          <div className="pt-3 border-t border-purple-100 space-y-2">
            {!user ? (
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onOpenLogin();
                  }}
                  className="flex items-center justify-center gap-1.5 py-3 text-xs font-bold text-purple-950 bg-white hover:bg-purple-50 border border-purple-200 rounded-xl shadow-2xs touch-manipulation min-h-[44px] cursor-pointer"
                >
                  <LogIn className="w-4 h-4 text-purple-600" />
                  <span>Login</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onOpenSignup();
                  }}
                  className="flex items-center justify-center gap-1.5 py-3 text-xs font-bold text-white bg-gradient-to-r from-pink-500 to-purple-600 hover:opacity-95 rounded-xl shadow-md touch-manipulation min-h-[44px] cursor-pointer"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>Sign Up</span>
                </button>
              </div>
            ) : (
              <div className="p-3 bg-purple-50 rounded-2xl flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold text-purple-950 overflow-hidden">
                  <div className="w-6 h-6 rounded-full bg-purple-600 text-white flex items-center justify-center text-xs font-bold shrink-0">
                    {user.name ? user.name[0].toUpperCase() : "D"}
                  </div>
                  <span className="truncate">{user.email}</span>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onLogout();
                  }}
                  className="px-3 py-1.5 text-xs font-bold text-rose-700 bg-rose-100 hover:bg-rose-200 rounded-lg touch-manipulation min-h-[36px] cursor-pointer"
                >
                  Logout
                </button>
              </div>
            )}

            {/* Workspace Link for Mobile */}
            <button
              type="button"
              onClick={() => {
                setMobileMenuOpen(false);
                onNavigateToWorkspace();
              }}
              className="w-full flex items-center justify-center gap-2 py-3 text-xs font-bold text-white bg-purple-950 hover:bg-purple-900 rounded-xl shadow-md touch-manipulation min-h-[44px] cursor-pointer"
            >
              <Sparkles className="w-4 h-4 text-pink-300" />
              <span>{user ? "Go to Verification Workspace" : "Cosmetic Verification"}</span>
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
