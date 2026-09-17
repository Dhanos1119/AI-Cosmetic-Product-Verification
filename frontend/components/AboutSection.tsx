"use client";

import { ShieldCheck, Award, Lock, Sparkles, BookOpen, Layers } from "lucide-react";

export default function AboutSection() {
  const techStack = [
    { name: "Next.js", type: "Frontend Framework" },
    { name: "TypeScript", type: "Language" },
    { name: "Node.js", type: "Runtime" },
    { name: "Express.js", type: "API Backend" },
    { name: "Python", type: "AI Services" },
    { name: "FastAPI", type: "Microservices" },
    { name: "PostgreSQL", type: "Database" },
    { name: "OCR", type: "Text Extraction" },
    { name: "CLIP / Image Similarity", type: "Visual Embeddings" },
    { name: "Fake Review Detection", type: "NLP Analysis" },
    { name: "Sentiment Analysis", type: "Opinion Mining" },
  ];

  return (
    <section id="about" className="py-16 md:py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="glass-card rounded-3xl p-8 sm:p-12 border border-purple-150 shadow-xl shadow-purple-900/5 relative overflow-hidden">
          {/* Background Decorative Blur */}
          <div className="absolute -top-16 -right-16 w-64 h-64 bg-pink-200/40 rounded-full blur-3xl pointer-events-none" />

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
            {/* Left Column: Project Mission & Details */}
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-purple-100/90 border border-purple-200 text-purple-950 text-xs font-semibold uppercase tracking-wider">
                <BookOpen className="w-3.5 h-3.5 text-purple-700" />
                <span>Academic Project Overview</span>
              </div>

              <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-snug">
                About <span className="bg-gradient-to-r from-pink-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent">CosmeticVerify</span>
              </h2>

              <p className="text-base sm:text-lg text-slate-600 leading-relaxed font-normal">
                <strong>AI Cosmetic Product Verification and Trustworthy Marketplace Recommendation System</strong> is developed as an academic solution for the <strong className="text-purple-950 font-semibold">Semester 6 Data Management Project</strong>.
              </p>

              <p className="text-sm sm:text-base text-slate-600 leading-relaxed font-normal">
                Our objective is to safeguard beauty consumers against counterfeit packaging, manipulated product representations, and deceptive seller feedback. By combining optical character extraction, visual similarity models, and sentiment analytics, CosmeticVerify surfaces certified stockists and verified product authenticity ratings.
              </p>

              {/* Stat Highlight Cards */}
              <div className="pt-2 grid grid-cols-1 sm:grid-cols-3 gap-4 text-slate-800">
                <div className="p-4 bg-white/80 rounded-2xl border border-purple-100 shadow-2xs flex items-center gap-3">
                  <ShieldCheck className="w-6 h-6 text-pink-600 shrink-0" />
                  <div>
                    <div className="text-[11px] text-slate-500 font-medium">Focus</div>
                    <div className="text-sm font-bold text-slate-900">Authenticity</div>
                  </div>
                </div>

                <div className="p-4 bg-white/80 rounded-2xl border border-purple-100 shadow-2xs flex items-center gap-3">
                  <Award className="w-6 h-6 text-purple-600 shrink-0" />
                  <div>
                    <div className="text-[11px] text-slate-500 font-medium">Goal</div>
                    <div className="text-sm font-bold text-slate-900">Review Trust</div>
                  </div>
                </div>

                <div className="p-4 bg-white/80 rounded-2xl border border-purple-100 shadow-2xs flex items-center gap-3">
                  <Lock className="w-6 h-6 text-indigo-600 shrink-0" />
                  <div>
                    <div className="text-[11px] text-slate-500 font-medium">Safety</div>
                    <div className="text-sm font-bold text-slate-900">Verified Stock</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Technology Stack Badges */}
            <div className="lg:col-span-5 space-y-5">
              <div className="p-6 bg-gradient-to-br from-purple-950 via-indigo-950 to-slate-950 text-white rounded-3xl space-y-4 shadow-xl border border-purple-900/60">
                <div className="flex items-center justify-between pb-3 border-b border-purple-800/80">
                  <div className="flex items-center gap-2">
                    <Layers className="w-4 h-4 text-pink-400" />
                    <h3 className="text-xs uppercase tracking-wider text-pink-300 font-bold">
                      System Technology Stack
                    </h3>
                  </div>
                  <Sparkles className="w-4 h-4 text-pink-400" />
                </div>

                <p className="text-xs text-purple-200">
                  Architecture components planned for backend and AI model integration:
                </p>

                {/* Tech Stack Pills List */}
                <div className="flex flex-wrap gap-2 pt-1">
                  {techStack.map((tech) => (
                    <span
                      key={tech.name}
                      className="px-3 py-1.5 rounded-xl bg-purple-900/70 hover:bg-purple-800 text-purple-100 border border-purple-700/60 text-xs font-semibold shadow-xs flex items-center gap-1.5"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-pink-400" />
                      <span>{tech.name}</span>
                    </span>
                  ))}
                </div>

                <div className="pt-3 border-t border-purple-800/80 text-[11px] text-purple-300 flex items-center justify-between">
                  <span>Semester 6 Data Management</span>
                  <span className="font-bold text-pink-300 bg-pink-950/60 px-2.5 py-0.5 rounded-full border border-pink-800/60">
                    Prototype v1.0
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
