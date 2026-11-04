"use client";

import { useEffect } from "react";
import { X, Sparkles, AlertCircle, Scan, ShieldAlert, MessageSquareWarning, Store } from "lucide-react";

export interface FeatureItem {
  id: string;
  title: string;
  description: string;
  badge: string;
  detailedOverview: string;
  plannedTechnologies: string[];
  demoStatus: string;
}

interface FeatureDetailModalProps {
  feature: FeatureItem | null;
  onClose: () => void;
}

export default function FeatureDetailModal({ feature, onClose }: FeatureDetailModalProps) {
  useEffect(() => {
    if (feature) {
      document.body.classList.add("overflow-hidden");
    } else {
      document.body.classList.remove("overflow-hidden");
    }
    return () => {
      document.body.classList.remove("overflow-hidden");
    };
  }, [feature]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && feature) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [feature, onClose]);

  if (!feature) return null;

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
        return Sparkles;
    }
  };

  const IconComponent = getFeatureIcon(feature.id);

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-3 sm:p-4 bg-[#0B0B12]/80 backdrop-blur-md overflow-y-auto animate-fadeIn pointer-events-auto modal-scroll-container"
      role="dialog"
      aria-modal="true"
      aria-labelledby="feature-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="relative w-full bg-[#191925] rounded-3xl shadow-2xl border border-[#303047] overflow-hidden my-auto text-[#F8FAFC] focus:outline-none z-[210] pointer-events-auto"
        style={{ width: "min(100% - 24px, 520px)", maxHeight: "calc(100dvh - 24px)" }}
      >
        {/* Modal Header */}
        <div className="p-5 sm:p-6 bg-gradient-to-r from-[#12121C] via-[#191925] to-[#202033] border-b border-[#303047] text-[#F8FAFC] relative shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="absolute top-4 right-4 text-[#A1A1B5] hover:text-[#F8FAFC] bg-[#202033] hover:bg-[#303047] p-2.5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[#A855F7] touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer z-10"
            aria-label="Close feature details modal"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-3 pr-10">
            <div className="w-12 h-12 rounded-2xl bg-[#EC4899]/15 border border-[#EC4899]/30 flex items-center justify-center text-[#EC4899] shrink-0">
              <IconComponent className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[10px] uppercase font-extrabold tracking-wider px-2.5 py-0.5 rounded-full bg-[#EC4899]/20 text-[#EC4899] border border-[#EC4899]/30">
                {feature.badge}
              </span>
              <h2 id="feature-modal-title" className="text-lg sm:text-xl font-bold text-[#F8FAFC] mt-1">
                {feature.title}
              </h2>
            </div>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-5 sm:p-7 space-y-5 overflow-y-auto" style={{ maxHeight: "calc(100dvh - 140px)" }}>
          <p className="text-xs sm:text-sm text-[#A1A1B5] leading-relaxed">
            {feature.detailedOverview}
          </p>

          {/* Planned Technologies Stack */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#A1A1B5]">
              Target Technical Stack
            </h4>
            <div className="flex flex-wrap gap-2">
              {feature.plannedTechnologies.map((tech) => (
                <span
                  key={tech}
                  className="text-xs font-semibold px-3 py-1 bg-[#12121C] text-[#F8FAFC] border border-[#303047] rounded-full"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>

          {/* Architecture Status Box */}
          <div className="p-4 bg-[#F59E0B]/10 border border-[#F59E0B]/30 rounded-2xl text-[#F59E0B] text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-[#F59E0B] shrink-0 mt-0.5" />
            <div className="text-[#A1A1B5]">
              <span className="font-bold text-[#F8FAFC]">Integrated Vision & NLP Architecture:</span> CLIP embeddings, EasyOCR extraction, and NLP sentiment pipelines operate end-to-end with the FastAPI backend.
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-[#12121C] border-t border-[#303047] flex justify-end shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 text-xs font-bold text-[#F8FAFC] bg-[#202033] hover:bg-[#303047] border border-[#303047] rounded-xl transition-colors touch-manipulation min-h-[44px] cursor-pointer"
          >
            Close Specification
          </button>
        </div>
      </div>
    </div>
  );
}
