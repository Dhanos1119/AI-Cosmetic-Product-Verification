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
      className="fixed inset-0 z-[200] flex items-center justify-center p-3 sm:p-4 bg-slate-900/70 backdrop-blur-md overflow-y-auto animate-fadeIn pointer-events-auto modal-scroll-container"
      role="dialog"
      aria-modal="true"
      aria-labelledby="feature-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="relative w-full bg-white rounded-3xl shadow-2xl border border-purple-150 overflow-hidden my-auto text-slate-900 focus:outline-none z-[210] pointer-events-auto"
        style={{ width: "min(100% - 24px, 520px)", maxHeight: "calc(100dvh - 24px)" }}
      >
        {/* Modal Header */}
        <div className="p-5 sm:p-6 bg-gradient-to-r from-purple-950 via-purple-900 to-slate-900 text-white relative shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="absolute top-4 right-4 text-purple-200 hover:text-white bg-white/10 hover:bg-white/20 p-2.5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-pink-400 touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer z-10"
            aria-label="Close feature details modal"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-3 pr-10">
            <div className="w-12 h-12 rounded-2xl bg-pink-500/20 border border-pink-400/40 flex items-center justify-center text-pink-300 shrink-0">
              <IconComponent className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[10px] uppercase font-extrabold tracking-wider px-2.5 py-0.5 rounded-full bg-pink-500/30 text-pink-200 border border-pink-400/30">
                {feature.badge}
              </span>
              <h2 id="feature-modal-title" className="text-lg sm:text-xl font-bold text-white mt-1">
                {feature.title}
              </h2>
            </div>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-5 sm:p-7 space-y-5 overflow-y-auto" style={{ maxHeight: "calc(100dvh - 140px)" }}>
          <p className="text-xs sm:text-sm text-slate-700 leading-relaxed">
            {feature.detailedOverview}
          </p>

          {/* Planned Technologies Stack */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Target Technical Stack
            </h4>
            <div className="flex flex-wrap gap-2">
              {feature.plannedTechnologies.map((tech) => (
                <span
                  key={tech}
                  className="text-xs font-semibold px-3 py-1 bg-purple-50 text-purple-950 border border-purple-200 rounded-full"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>

          {/* Disclaimer Box */}
          <div className="p-4 bg-amber-50 border border-amber-200/90 rounded-2xl text-amber-900 text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Demo Architecture Spec:</span> Models and machine learning pipelines for this module are currently simulated. Full neural network integration will be deployed in the backend stage.
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 text-xs font-bold text-slate-700 bg-white hover:bg-slate-100 border border-slate-300 rounded-xl transition-colors touch-manipulation min-h-[44px] cursor-pointer"
          >
            Close Specification
          </button>
        </div>
      </div>
    </div>
  );
}
