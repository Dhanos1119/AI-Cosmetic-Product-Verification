"use client";

import { UploadCloud, FileText, CheckCheck, ShoppingBag, ArrowRight } from "lucide-react";

export default function HowItWorks() {
  const steps = [
    {
      stepNumber: "01",
      title: "Upload Product Image",
      description: "Take or select a clear photo of the cosmetic package, front/back label, or packaging container.",
      icon: UploadCloud,
    },
    {
      stepNumber: "02",
      title: "Extract Product Information",
      description: "Our system parses key brand names, text details, batch numbers, and ingredient lists.",
      icon: FileText,
    },
    {
      stepNumber: "03",
      title: "Verify Product and Reviews",
      description: "Cross-reference authentic product data, detect manipulated imagery, and evaluate review credibility.",
      icon: CheckCheck,
    },
    {
      stepNumber: "04",
      title: "Recommend the Most Trustworthy Platform",
      description: "Receive a trust summary and direct links to certified marketplaces with genuine stock.",
      icon: ShoppingBag,
    },
  ];

  return (
    <section id="how-it-works" className="py-16 md:py-24 bg-[#0B0B12] text-[#F8FAFC]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center space-y-3 mb-16">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-[#191925] border border-[#303047] text-[#EC4899] text-xs font-semibold uppercase tracking-wider">
            <span>Simple 4-Step Process</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F8FAFC] tracking-tight">
            How It Works
          </h2>
          <p className="text-[#A1A1B5] max-w-2xl mx-auto text-base">
            From product photo upload to certified marketplace recommendation in four streamlined steps.
          </p>
        </div>

        {/* Steps Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 relative">
          {steps.map((step, index) => {
            const StepIcon = step.icon;
            return (
              <div key={step.stepNumber} className="relative flex flex-col h-full">
                <div className="rounded-3xl p-6 sm:p-8 flex-1 flex flex-col justify-between border border-[#303047] bg-[#191925] shadow-xl hover:border-[#A855F7]/50 transition-all">
                  <div>
                    {/* Step Number & Icon */}
                    <div className="flex items-center justify-between mb-6">
                      <span className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-[#EC4899] to-[#A855F7]">
                        {step.stepNumber}
                      </span>
                      <div className="w-12 h-12 rounded-2xl bg-[#202033] border border-[#303047] flex items-center justify-center text-[#A855F7]">
                        <StepIcon className="w-6 h-6" />
                      </div>
                    </div>

                    {/* Step Content */}
                    <h3 className="text-lg font-bold text-[#F8FAFC] mb-2 leading-snug">
                      {step.title}
                    </h3>
                    <p className="text-sm text-[#A1A1B5] leading-relaxed font-normal">
                      {step.description}
                    </p>
                  </div>

                  <div className="mt-6 pt-4 border-t border-[#303047] flex items-center text-xs font-bold text-[#EC4899]">
                    <span>Step {index + 1} of 4</span>
                  </div>
                </div>

                {/* Arrow Connector for Desktop view */}
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute -right-4 top-1/2 -translate-y-1/2 z-10 text-[#303047] pointer-events-none">
                    <ArrowRight className="w-6 h-6" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
