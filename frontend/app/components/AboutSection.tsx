"use client";

import { ShieldCheck, Award, Lock, Sparkles, BookOpen } from "lucide-react";

export default function AboutSection() {
  return (
    <section id="about" className="py-16 md:py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="glass-card rounded-3xl p-8 sm:p-12 border border-purple-150 shadow-xl shadow-purple-900/5 relative overflow-hidden">
          {/* Subtle Background Glow */}
          <div className="absolute -top-16 -right-16 w-64 h-64 bg-pink-200/40 rounded-full blur-3xl pointer-events-none" />

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-purple-100/90 border border-purple-200 text-purple-950 text-xs font-semibold uppercase tracking-wider">
                <BookOpen className="w-3.5 h-3.5 text-purple-700" />
                <span>Academic Project Overview</span>
              </div>

              <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-snug">
                About <span className="bg-gradient-to-r from-pink-600 to-purple-600 bg-clip-text text-transparent">CosmeticVerify</span>
              </h2>

              <p className="text-base sm:text-lg text-slate-600 leading-relaxed font-normal">
                CosmeticVerify is developed as part of the <strong className="text-slate-900 font-semibold">Semester 6 Data Management Project</strong>. The system addresses growing market concerns regarding counterfeit cosmetics, manipulated online product images, and deceptive seller reviews.
              </p>

              <p className="text-sm sm:text-base text-slate-600 leading-relaxed font-normal">
                By combining image feature processing, text analytics, and marketplace trust metrics, our platform empowers beauty consumers to shop safely and locate authentic cosmetic stock across trusted e-commerce platforms.
              </p>

              <div className="pt-2 grid grid-cols-1 sm:grid-cols-3 gap-4 text-slate-800">
                <div className="p-4 bg-white/80 rounded-2xl border border-purple-100 shadow-2xs flex items-center gap-3">
                  <ShieldCheck className="w-6 h-6 text-pink-600 shrink-0" />
                  <div>
                    <div className="text-xs text-slate-500 font-medium">Focus</div>
                    <div className="text-sm font-bold text-slate-900">Authenticity</div>
                  </div>
                </div>

                <div className="p-4 bg-white/80 rounded-2xl border border-purple-100 shadow-2xs flex items-center gap-3">
                  <Award className="w-6 h-6 text-purple-600 shrink-0" />
                  <div>
                    <div className="text-xs text-slate-500 font-medium">Goal</div>
                    <div className="text-sm font-bold text-slate-900">Review Trust</div>
                  </div>
                </div>

                <div className="p-4 bg-white/80 rounded-2xl border border-purple-100 shadow-2xs flex items-center gap-3">
                  <Lock className="w-6 h-6 text-indigo-600 shrink-0" />
                  <div>
                    <div className="text-xs text-slate-500 font-medium">Safety</div>
                    <div className="text-sm font-bold text-slate-900">Verified Stock</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="lg:col-span-5">
              <div className="p-6 bg-gradient-to-br from-purple-900 via-indigo-900 to-slate-900 text-white rounded-2xl space-y-4 shadow-lg">
                <div className="flex items-center justify-between pb-3 border-b border-purple-800">
                  <span className="text-xs uppercase tracking-wider text-pink-300 font-semibold">Project Metadata</span>
                  <Sparkles className="w-4 h-4 text-pink-400" />
                </div>

                <div className="space-y-3 text-xs sm:text-sm">
                  <div className="flex justify-between py-1 border-b border-purple-800/60">
                    <span className="text-purple-300">Project Title:</span>
                    <span className="font-semibold text-white text-right">AI Cosmetic Product Verification</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-purple-800/60">
                    <span className="text-purple-300">Course / Module:</span>
                    <span className="font-semibold text-white">Semester 6 Data Management</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-purple-800/60">
                    <span className="text-purple-300">Interface Version:</span>
                    <span className="font-semibold text-pink-300">v1.0 (Frontend Prototype)</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-purple-300">Status:</span>
                    <span className="font-semibold text-emerald-400">UI / Mock Data Ready</span>
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
