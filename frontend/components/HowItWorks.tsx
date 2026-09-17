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
    <section id="how-it-works" className="py-16 md:py-24 bg-gradient-to-b from-purple-50/50 via-pink-50/30 to-transparent">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center space-y-3 mb-16">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-100/80 border border-purple-200 text-purple-900 text-xs font-semibold uppercase tracking-wider">
            <span>Simple 4-Step Process</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            How It Works
          </h2>
          <p className="text-slate-600 max-w-2xl mx-auto text-base">
            From product photo upload to certified marketplace recommendation in four streamlined steps.
          </p>
        </div>

        {/* Steps Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 relative">
          {steps.map((step, index) => {
            const StepIcon = step.icon;
            return (
              <div key={step.stepNumber} className="relative flex flex-col h-full">
                <div className="glass-card rounded-3xl p-6 sm:p-8 flex-1 flex flex-col justify-between border border-purple-100/90 shadow-sm hover:shadow-md transition-shadow">
                  <div>
                    {/* Step Number & Icon */}
                    <div className="flex items-center justify-between mb-6">
                      <span className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-pink-500 to-purple-600">
                        {step.stepNumber}
                      </span>
                      <div className="w-12 h-12 rounded-2xl bg-purple-100/80 flex items-center justify-center text-purple-700">
                        <StepIcon className="w-6 h-6" />
                      </div>
                    </div>

                    {/* Step Content */}
                    <h3 className="text-lg font-bold text-slate-900 mb-2 leading-snug">
                      {step.title}
                    </h3>
                    <p className="text-sm text-slate-600 leading-relaxed font-normal">
                      {step.description}
                    </p>
                  </div>

                  <div className="mt-6 pt-4 border-t border-purple-100/60 flex items-center text-xs font-bold text-pink-600">
                    <span>Step {index + 1} of 4</span>
                  </div>
                </div>

                {/* Arrow Connector for Desktop view */}
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute -right-4 top-1/2 -translate-y-1/2 z-10 text-purple-300 pointer-events-none">
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
