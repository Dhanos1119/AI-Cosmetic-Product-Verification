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
    <section id="about" className="py-16 md:py-24 bg-[#0B0B12] text-[#F8FAFC]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-3xl p-8 sm:p-12 border border-[#303047] bg-[#191925] shadow-2xl relative overflow-hidden">
          {/* Subtle Accent Glow */}
          <div className="absolute -top-16 -right-16 w-64 h-64 bg-purple-900/20 rounded-full blur-3xl pointer-events-none" />

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
            {/* Left Column: Project Mission & Details */}
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#202033] border border-[#303047] text-[#EC4899] text-xs font-semibold uppercase tracking-wider">
                <BookOpen className="w-3.5 h-3.5 text-[#EC4899]" />
                <span>Platform Overview</span>
              </div>

              <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F8FAFC] tracking-tight leading-snug">
                About <span className="bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-[#8B5CF6] bg-clip-text text-transparent">CosmeticVerify</span>
              </h2>

              <p className="text-base sm:text-lg text-[#A1A1B5] leading-relaxed font-normal">
                <strong className="text-[#F8FAFC]">CosmeticVerify</strong> is an independent AI-powered cosmetic product verification and trustworthy marketplace recommendation platform.
              </p>

              <p className="text-sm sm:text-base text-[#A1A1B5] leading-relaxed font-normal">
                Our objective is to safeguard beauty consumers against counterfeit packaging, unverified product representations, and deceptive seller feedback. By combining optical character extraction, visual similarity models, and sentiment analytics, CosmeticVerify surfaces certified stockists and verified product authenticity ratings.
              </p>

              {/* Stat Highlight Cards */}
              <div className="pt-2 grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 bg-[#12121C] rounded-2xl border border-[#303047] shadow-xs flex items-center gap-3">
                  <ShieldCheck className="w-6 h-6 text-[#EC4899] shrink-0" />
                  <div>
                    <div className="text-[11px] text-[#A1A1B5] font-medium">Focus</div>
                    <div className="text-sm font-bold text-[#F8FAFC]">Authenticity</div>
                  </div>
                </div>

                <div className="p-4 bg-[#12121C] rounded-2xl border border-[#303047] shadow-xs flex items-center gap-3">
                  <Award className="w-6 h-6 text-[#A855F7] shrink-0" />
                  <div>
                    <div className="text-[11px] text-[#A1A1B5] font-medium">Goal</div>
                    <div className="text-sm font-bold text-[#F8FAFC]">Review Trust</div>
                  </div>
                </div>

                <div className="p-4 bg-[#12121C] rounded-2xl border border-[#303047] shadow-xs flex items-center gap-3">
                  <Lock className="w-6 h-6 text-[#8B5CF6] shrink-0" />
                  <div>
                    <div className="text-[11px] text-[#A1A1B5] font-medium">Safety</div>
                    <div className="text-sm font-bold text-[#F8FAFC]">Verified Stock</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right Column: Technology Stack Badges */}
            <div className="lg:col-span-5 space-y-5">
              <div className="p-6 bg-[#202033] text-[#F8FAFC] rounded-3xl space-y-4 shadow-xl border border-[#303047]">
                <div className="flex items-center justify-between pb-3 border-b border-[#303047]">
                  <div className="flex items-center gap-2">
                    <Layers className="w-4 h-4 text-[#EC4899]" />
                    <h3 className="text-xs uppercase tracking-wider text-[#EC4899] font-bold">
                      System Technology Stack
                    </h3>
                  </div>
                  <Sparkles className="w-4 h-4 text-[#A855F7]" />
                </div>

                <p className="text-xs text-[#A1A1B5]">
                  Integrated architecture components across backend, database, and AI pipelines:
                </p>

                {/* Tech Stack Pills List */}
                <div className="flex flex-wrap gap-2 pt-1">
                  {techStack.map((tech) => (
                    <span
                      key={tech.name}
                      className="px-3 py-1.5 rounded-xl bg-[#12121C] hover:bg-[#191925] text-[#F8FAFC] border border-[#303047] text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-colors"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-[#EC4899]" />
                      <span>{tech.name}</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
