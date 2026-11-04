"use client";

import { useState, useEffect } from "react";
import { ShieldCheck, Sparkles, Menu, X, LogIn, LogOut, User, UserPlus, CheckCircle2 } from "lucide-react";

interface HeaderProps {
  user: { email: string; name?: string; username?: string; full_name?: string } | null;
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

  // Authenticated username greeting resolution
  const username =
    user?.name?.trim() ||
    user?.username?.trim() ||
    user?.full_name?.trim() ||
    (user?.email ? user.email.split("@")[0] : "") ||
    "User";

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
            className="flex items-center gap-2.5 group focus:outline-none focus:ring-2 focus:ring-[#A855F7] rounded-xl p-1 touch-manipulation cursor-pointer"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#EC4899] via-[#A855F7] to-indigo-600 flex items-center justify-center text-white shadow-md shadow-pink-500/20 group-hover:scale-105 transition-transform duration-200">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-bold tracking-tight text-[#F8FAFC]">
                Cosmetic<span className="text-[#EC4899] font-extrabold">Verify</span>
              </span>
              <span className="text-[10px] uppercase tracking-wider font-semibold text-[#A855F7] -mt-1">
                AI Authenticity System
              </span>
            </div>
          </a>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-1 bg-[#12121C] p-1.5 rounded-full border border-[#303047]">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                onClick={(e) => {
                  e.preventDefault();
                  handleNavClick(link.href);
                }}
                className="px-4 py-2 text-xs sm:text-sm font-medium text-[#A1A1B5] rounded-full hover:text-[#F8FAFC] hover:bg-[#191925] hover:shadow-xs transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#A855F7] touch-manipulation cursor-pointer"
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
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-[#F8FAFC] bg-[#191925] hover:bg-[#202033] border border-[#303047] rounded-full shadow-2xs transition-all touch-manipulation min-h-[40px] cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#A855F7]"
                >
                  <LogIn className="w-3.5 h-3.5 text-[#A855F7]" />
                  <span>Login</span>
                </button>

                <button
                  type="button"
                  onClick={onOpenSignup}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-indigo-600 rounded-full shadow-md hover:opacity-95 transition-all touch-manipulation min-h-[40px] cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#A855F7]"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>Sign Up</span>
                </button>
              </div>
            ) : (
              /* LOGGED-IN STATE CONTROLS (Desktop) */
              <div className="flex items-center gap-3">
                <span className="hidden sm:inline-block text-xs font-semibold text-[#F8FAFC] px-3.5 py-1.5 bg-[#191925] border border-[#303047] rounded-full shadow-2xs whitespace-nowrap">
                  Hi, {username}
                </span>

                <button
                  type="button"
                  onClick={onLogout}
                  className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-[#F87171] bg-[#191925] hover:bg-[#202033] border border-[#303047] rounded-full transition-colors touch-manipulation min-h-[38px] cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#F87171]"
                  title="Logout"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Logout</span>
                </button>
              </div>
            )}

            {/* Workspace CTA Button */}
            <button
              type="button"
              onClick={onNavigateToWorkspace}
              className="hidden sm:inline-flex items-center justify-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-gradient-to-r from-[#A855F7] to-[#EC4899] hover:opacity-95 rounded-full shadow-md transition-all touch-manipulation min-h-[40px] cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#A855F7]"
            >
              <Sparkles className="w-3.5 h-3.5 text-white animate-pulse" />
              <span>{user ? "Go to Workspace" : "Verification"}</span>
            </button>

            {/* Mobile Hamburger Toggle Button */}
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2.5 rounded-xl text-[#F8FAFC] bg-[#191925] border border-[#303047] hover:bg-[#202033] focus:outline-none focus:ring-2 focus:ring-[#A855F7] transition-colors touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer relative z-50"
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
        <div className="md:hidden relative z-45 bg-[#12121C] border-t border-[#303047] shadow-xl px-4 pt-3 pb-6 space-y-3 animate-fadeIn">
          {navLinks.map((link) => (
            <a
              key={link.name}
              href={link.href}
              onClick={(e) => {
                e.preventDefault();
                handleNavClick(link.href);
              }}
              className="block px-4 py-3 text-base font-semibold text-[#F8FAFC] hover:bg-[#191925] active:bg-[#202033] rounded-xl transition-colors touch-manipulation min-h-[44px] cursor-pointer"
            >
              {link.name}
            </a>
          ))}

          {/* User state in mobile dropdown */}
          <div className="pt-3 border-t border-[#303047] space-y-2">
            {!user ? (
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onOpenLogin();
                  }}
                  className="flex items-center justify-center gap-1.5 py-3 text-xs font-bold text-[#F8FAFC] bg-[#191925] hover:bg-[#202033] border border-[#303047] rounded-xl shadow-2xs touch-manipulation min-h-[44px] cursor-pointer"
                >
                  <LogIn className="w-4 h-4 text-[#A855F7]" />
                  <span>Login</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onOpenSignup();
                  }}
                  className="flex items-center justify-center gap-1.5 py-3 text-xs font-bold text-white bg-gradient-to-r from-[#EC4899] to-[#A855F7] hover:opacity-95 rounded-xl shadow-md touch-manipulation min-h-[44px] cursor-pointer"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>Sign Up</span>
                </button>
              </div>
            ) : (
              <div className="p-3 bg-[#191925] border border-[#303047] rounded-2xl flex items-center justify-between gap-3">
                <span className="text-xs font-semibold text-[#F8FAFC] whitespace-nowrap">
                  Hi, {username}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    onLogout();
                  }}
                  className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-bold text-[#F87171] bg-[#12121C] hover:bg-[#202033] border border-[#303047] rounded-xl touch-manipulation min-h-[36px] cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Logout</span>
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
              className="w-full flex items-center justify-center gap-2 py-3 text-xs font-bold text-white bg-gradient-to-r from-[#A855F7] to-[#EC4899] rounded-xl shadow-md touch-manipulation min-h-[44px] cursor-pointer"
            >
              <Sparkles className="w-4 h-4 text-white" />
              <span>{user ? "Go to Verification Workspace" : "Cosmetic Verification"}</span>
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
