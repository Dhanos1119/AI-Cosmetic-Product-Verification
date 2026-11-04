"use client";

import { ShieldCheck, ArrowRight, Sparkles, CheckCircle2, ShoppingBag, Lock, UserCheck } from "lucide-react";

interface HeroProps {
  user: { email: string; name: string } | null;
  onStartVerification: () => void;
  onHowItWorks: () => void;
}

export default function Hero({ user, onStartVerification, onHowItWorks }: HeroProps) {
  return (
    <section id="hero" className="relative overflow-hidden pt-12 pb-16 md:pt-20 md:pb-24 bg-[#0B0B12]">
      {/* Background Decorative Gradient Mesh */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-96 pointer-events-none -z-10">
        <div className="absolute top-4 left-1/4 w-80 h-80 bg-[#EC4899]/15 rounded-full blur-3xl" />
        <div className="absolute top-12 right-1/4 w-96 h-96 bg-[#A855F7]/15 rounded-full blur-3xl" />
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Left Column: Content */}
          <div className="lg:col-span-7 flex flex-col items-start text-left space-y-6">
            {/* Pill Tag */}
            {!user ? (
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#191925] border border-[#303047] text-[#EC4899] text-xs font-semibold tracking-wide uppercase">
                <Sparkles className="w-3.5 h-3.5 text-[#EC4899]" />
                <span>Smart Beauty Authenticity & Trust</span>
              </div>
            ) : (
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#191925] border border-[#303047] text-[#A855F7] text-xs font-bold tracking-wide uppercase">
                <UserCheck className="w-3.5 h-3.5 text-[#A855F7]" />
                <span>Signed In • Verification Workspace Active</span>
              </div>
            )}

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-[#F8FAFC] tracking-tight leading-[1.15]">
              {!user ? (
                <>
                  Verify Your Cosmetics.{" "}
                  <span className="bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-indigo-400 bg-clip-text text-transparent block sm:inline">
                    Shop With Confidence.
                  </span>
                </>
              ) : (
                <>
                  Welcome back to{" "}
                  <span className="bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-indigo-400 bg-clip-text text-transparent block sm:inline">
                    CosmeticVerify.
                  </span>
                </>
              )}
            </h1>

            {/* Sub-description */}
            <p className="text-lg sm:text-xl text-[#A1A1B5] leading-relaxed max-w-2xl font-normal">
              {!user ? (
                "Upload a cosmetic product image and discover product details, review trust, and reliable marketplace recommendations."
              ) : (
                "You are ready to verify your cosmetic products. Upload a packaging photo or use your camera to start instant inspection."
              )}
            </p>

            {/* Key Value Props Pills */}
            <div className="flex flex-wrap items-center gap-y-2 gap-x-4 pt-1 text-sm text-[#F8FAFC] font-medium">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-[#EC4899]" />
                <span>Instant Image Parsing</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-[#A855F7]" />
                <span>Fake Review Detection</span>
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-[#22C55E]" />
                <span>Certified Sellers</span>
              </div>
            </div>

            {/* Hero CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 pt-4 w-full sm:w-auto">
              <button
                type="button"
                onClick={onStartVerification}
                className="inline-flex items-center justify-center gap-2.5 px-8 py-4 text-base font-bold text-white bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-indigo-600 rounded-2xl shadow-lg shadow-purple-900/30 hover:shadow-xl hover:shadow-purple-900/50 hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200 text-center touch-manipulation min-h-[48px] cursor-pointer"
              >
                <span>Start Verification</span>
                <ArrowRight className="w-5 h-5" />
              </button>

              <button
                type="button"
                onClick={onHowItWorks}
                className="inline-flex items-center justify-center gap-2 px-7 py-4 text-base font-semibold text-[#F8FAFC] bg-[#191925] hover:bg-[#202033] border border-[#303047] rounded-2xl shadow-xs hover:border-[#A855F7]/50 transition-all duration-200 text-center touch-manipulation min-h-[48px] cursor-pointer"
              >
                <span>{user ? "Open Verification Workspace" : "How It Works"}</span>
              </button>
            </div>
          </div>

          {/* Right Column: Visual Demo Showcase Card */}
          <div className="lg:col-span-5 w-full">
            <div className="relative mx-auto max-w-md lg:max-w-none">
              <div className="glass-card rounded-3xl p-6 sm:p-8 shadow-2xl shadow-purple-950/40 border border-[#303047] bg-[#191925]/90 relative overflow-hidden">
                <div className="flex items-center justify-between pb-4 border-b border-[#303047]">
                  <div className="flex items-center gap-2.5">
                    <div className="w-3 h-3 rounded-full bg-[#EC4899]" />
                    <div className="w-3 h-3 rounded-full bg-[#A855F7]" />
                    <div className="w-3 h-3 rounded-full bg-indigo-500" />
                  </div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-[#A855F7] bg-[#12121C] border border-[#303047] px-2.5 py-1 rounded-full">
                    {user ? "Workspace Active" : "Cosmetic Engine Preview"}
                  </span>
                </div>

                <div className="mt-6 space-y-4">
                  <div className="p-4 bg-[#12121C] rounded-2xl border border-[#303047] flex items-center gap-4">
                    <div className="w-14 h-14 rounded-xl bg-[#202033] flex items-center justify-center text-[#EC4899] border border-[#303047] shrink-0">
                      <ShoppingBag className="w-7 h-7 text-[#EC4899]" />
                    </div>
                    <div>
                      <div className="text-xs font-semibold text-[#EC4899] uppercase tracking-wider">Product Visual Check</div>
                      <div className="text-sm font-bold text-[#F8FAFC]">Foundation & Skincare Inspection</div>
                      <div className="text-xs text-[#A1A1B5] mt-0.5">Automated packaging & brand verification</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3.5 bg-[#202033] rounded-xl border border-[#303047]">
                      <div className="text-xs text-[#A1A1B5] font-medium">Review Trust</div>
                      <div className="text-base font-bold text-[#F8FAFC] mt-0.5">High Confidence</div>
                      <div className="text-[11px] text-[#22C55E] font-semibold mt-1">✓ Verified sentiment</div>
                    </div>
                    <div className="p-3.5 bg-[#202033] rounded-xl border border-[#303047]">
                      <div className="text-xs text-[#A1A1B5] font-medium">Market Safety</div>
                      <div className="text-base font-bold text-[#F8FAFC] mt-0.5">Top Retailers</div>
                      <div className="text-[11px] text-[#A855F7] font-semibold mt-1">✓ Cross-marketplace</div>
                    </div>
                  </div>

                  <div className="p-3 bg-[#12121C] border border-[#303047] text-[#F8FAFC] rounded-xl text-xs flex items-center justify-between">
                    <span className="flex items-center gap-1.5 font-medium">
                      <ShieldCheck className="w-4 h-4 text-[#EC4899]" />
                      Smart Verification Shield
                    </span>
                    <span className="text-[#A855F7] font-bold flex items-center gap-1">
                      {user ? "Ready to Scan" : <Lock className="w-3.5 h-3.5" />}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
