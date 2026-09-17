"use client";

import { Scan, ShieldAlert, MessageSquareWarning, Store } from "lucide-react";

export default function Features() {
  const features = [
    {
      id: "product-identification",
      title: "Product Identification",
      description: "Extract packaging details, formula attributes, brand logos, and batch identifiers from uploaded cosmetic images.",
      icon: Scan,
      gradient: "from-pink-500 to-rose-500",
      bgLight: "bg-pink-50/60",
      borderColor: "border-pink-100",
      badge: "Vision AI",
    },
    {
      id: "image-verification",
      title: "Image Verification",
      description: "Detect potential image manipulation, altered text, and fraudulent packaging representations using visual analysis models.",
      icon: ShieldAlert,
      gradient: "from-purple-500 to-indigo-600",
      bgLight: "bg-purple-50/60",
      borderColor: "border-purple-100",
      badge: "Authenticity",
    },
    {
      id: "fake-review-detection",
      title: "Fake Review Detection",
      description: "Analyze cross-platform customer feedback to identify artificially boosted ratings, bot patterns, and deceptive reviews.",
      icon: MessageSquareWarning,
      gradient: "from-indigo-500 to-purple-600",
      bgLight: "bg-indigo-50/60",
      borderColor: "border-indigo-100",
      badge: "Review Trust",
    },
    {
      id: "marketplace-recommendation",
      title: "Trustworthy Marketplace Recommendation",
      description: "Guide consumers to verified sellers and certified e-commerce platforms with authentic stock and seller safety guarantees.",
      icon: Store,
      gradient: "from-pink-600 to-purple-600",
      bgLight: "bg-pink-50/60",
      borderColor: "border-pink-100",
      badge: "Safe Shopping",
    },
  ];

  return (
    <section id="features" className="py-16 md:py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center space-y-3 mb-16">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-pink-100/80 border border-pink-200 text-pink-900 text-xs font-semibold uppercase tracking-wider">
            <span>Key System Capabilities</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            Comprehensive Cosmetic Verification
          </h2>
          <p className="text-slate-600 max-w-2xl mx-auto text-base">
            Intelligent features designed to ensure beauty product authenticity and enhance shopper trust.
          </p>
        </div>

        {/* 4 Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
          {features.map((feature) => {
            const IconComponent = feature.icon;
            return (
              <div
                key={feature.id}
                className={`glass-card rounded-3xl p-6 sm:p-8 flex flex-col justify-between hover:shadow-xl hover:shadow-purple-900/5 hover:-translate-y-1 transition-all duration-300 border ${feature.borderColor}`}
              >
                <div className="space-y-5">
                  {/* Icon & Badge Header */}
                  <div className="flex items-center justify-between">
                    <div
                      className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center text-white shadow-md shadow-purple-500/20`}
                    >
                      <IconComponent className="w-7 h-7" />
                    </div>
                    <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-white border border-purple-150 text-purple-900 shadow-2xs">
                      {feature.badge}
                    </span>
                  </div>

                  {/* Title & Description */}
                  <div className="space-y-2.5">
                    <h3 className="text-xl font-bold text-slate-900 leading-snug">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-slate-600 leading-relaxed font-normal">
                      {feature.description}
                    </p>
                  </div>
                </div>

                {/* Footer Accent Line */}
                <div className="mt-6 pt-4 border-t border-purple-100/60 flex items-center justify-between text-xs font-semibold text-purple-700">
                  <span>Module Spec</span>
                  <span className="w-2 h-2 rounded-full bg-pink-500" />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
