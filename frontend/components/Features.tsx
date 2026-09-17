"use client";

import { Scan, ShieldAlert, MessageSquareWarning, Store, ArrowRight } from "lucide-react";
import { FeatureItem } from "./FeatureDetailModal";

interface FeaturesProps {
  onSelectFeature: (feature: FeatureItem) => void;
}

export default function Features({ onSelectFeature }: FeaturesProps) {
  const featureItems: FeatureItem[] = [
    {
      id: "product-identification",
      title: "Product Identification",
      description: "Extract packaging details, formula attributes, brand logos, and batch identifiers from uploaded cosmetic images.",
      badge: "Vision AI",
      detailedOverview:
        "The Product Identification module uses computer vision and optical character recognition (OCR) algorithms to parse text on cosmetic containers, analyze brand logos, and extract batch codes for identity matching.",
      plannedTechnologies: ["OCR", "Tesseract / EasyOCR", "OpenCV", "FastAPI"],
      demoStatus: "Frontend Spec Mode (Backend Connection Pending)",
    },
    {
      id: "image-verification",
      title: "Image Verification",
      description: "Detect potential image manipulation, altered text, and fraudulent packaging representations using visual analysis models.",
      badge: "Authenticity",
      detailedOverview:
        "The Image Verification engine leverages CLIP-based image embedding and forgery detection algorithms to flag tampered images, altered product dimensions, and non-authentic digital mockups.",
      plannedTechnologies: ["CLIP Model", "PyTorch", "Visual Feature Vectors", "Python"],
      demoStatus: "Frontend Spec Mode (Backend Connection Pending)",
    },
    {
      id: "fake-review-detection",
      title: "Fake Review Detection",
      description: "Analyze cross-platform customer feedback to identify artificially boosted ratings, bot patterns, and deceptive reviews.",
      badge: "Review Trust",
      detailedOverview:
        "The Fake Review Detection system applies Natural Language Processing (NLP) and sentiment analysis to identify suspicious rating clusters, duplicate text patterns, and automated bot reviews across e-commerce listings.",
      plannedTechnologies: ["BERT / RoBERTa", "Sentiment Analysis", "NLP Pipelines", "PostgreSQL"],
      demoStatus: "Frontend Spec Mode (Backend Connection Pending)",
    },
    {
      id: "marketplace-recommendation",
      title: "Trustworthy Marketplace Recommendation",
      description: "Guide consumers to verified sellers and certified e-commerce platforms with authentic stock and seller safety guarantees.",
      badge: "Safe Shopping",
      detailedOverview:
        "The Recommendation Engine ranks authorized stockists, verified seller ratings, and real-time merchant safety metrics to match consumers with authentic purchasing channels.",
      plannedTechnologies: ["Recommendation Matrix", "Seller Verification Index", "PostgreSQL API"],
      demoStatus: "Frontend Spec Mode (Backend Connection Pending)",
    },
  ];

  const getFeatureIcon = (id: string) => {
    switch (id) {
      case "product-identification":
        return Scan;
      case "image-verification":
        return ShieldAlert;
      case "fake-review-detection":
        return MessageSquareWarning;
      case "marketplace-recommendation":
        return Store;
      default:
        return Scan;
    }
  };

  return (
    <section id="features" className="py-16 md:py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center space-y-3 mb-16">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-pink-100/80 border border-pink-200 text-pink-900 text-xs font-semibold uppercase tracking-wider">
            <span>System Capabilities</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            Comprehensive Cosmetic Verification
          </h2>
          <p className="text-slate-600 max-w-2xl mx-auto text-base">
            Intelligent modules designed to ensure cosmetic authenticity and protect beauty shoppers online.
          </p>
        </div>

        {/* 4 Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
          {featureItems.map((item) => {
            const IconComponent = getFeatureIcon(item.id);
            return (
              <div
                key={item.id}
                className="glass-card rounded-3xl p-6 sm:p-8 flex flex-col justify-between hover:shadow-xl hover:shadow-purple-900/5 hover:-translate-y-1 transition-all duration-300 border border-purple-100"
              >
                <div className="space-y-5">
                  {/* Icon & Badge Header */}
                  <div className="flex items-center justify-between">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-pink-500 via-purple-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-purple-500/20">
                      <IconComponent className="w-7 h-7" />
                    </div>
                    <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-white border border-purple-150 text-purple-900 shadow-2xs">
                      {item.badge}
                    </span>
                  </div>

                  {/* Title & Description */}
                  <div className="space-y-2.5">
                    <h3 className="text-xl font-bold text-slate-900 leading-snug">
                      {item.title}
                    </h3>
                    <p className="text-sm text-slate-600 leading-relaxed font-normal">
                      {item.description}
                    </p>
                  </div>
                </div>

                {/* Learn More Action Button */}
                <div className="mt-6 pt-4 border-t border-purple-100/60">
                  <button
                    type="button"
                    onClick={() => onSelectFeature(item)}
                    className="w-full flex items-center justify-between px-4 py-2.5 rounded-xl bg-purple-50 hover:bg-purple-100 text-purple-950 text-xs font-bold transition-colors group touch-manipulation min-h-[44px] cursor-pointer"
                  >
                    <span>Learn More</span>
                    <ArrowRight className="w-4 h-4 text-purple-600 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
