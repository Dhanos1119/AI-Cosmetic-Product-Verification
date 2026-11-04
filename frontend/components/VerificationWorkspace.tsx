"use client";

import { useEffect, useState } from "react";
import {
  Lock,
  LogIn,
  UserPlus,
  ShieldCheck,
  Sparkles,
  Loader2,
  AlertCircle,
  Sparkle,
  XCircle,
  Scan,
  Cpu,
  Layers,
  Store,
  CheckCircle2,
} from "lucide-react";
import ImageUploader from "./ImageUploader";
import VerificationResult, { AiAnalysisResult } from "./VerificationResult";

interface VerificationWorkspaceProps {
  user: { email: string; name: string } | null;
  selectedFile: File | null;
  previewUrl: string | null;
  productUrl?: string;
  onProductUrlChange?: (url: string) => void;
  aiAnalysisResult: AiAnalysisResult | null;
  analysisError?: string | null;
  isAnalyzing: boolean;
  hasVerified: boolean;
  onFileSelect: (file: File) => void;
  onFileRemove: () => void;
  onOpenCamera: () => void;
  onStartVerification: (e?: React.MouseEvent) => void;
  onCancelVerification?: () => void;
  onResetVerification: () => void;
  onOpenLogin: () => void;
  onOpenSignup: () => void;
}

const PROCESSING_STAGES = [
  { id: "prep", label: "Image validation & dimension downscaling", icon: Scan },
  { id: "ocr", label: "Optical Character Recognition & brand extraction", icon: Cpu },
  { id: "clip", label: "CLIP visual embedding & cosmetic category identification", icon: Layers },
  { id: "market", label: "Marketplace catalog cross-referencing", icon: Store },
  { id: "auth", label: "Multi-tier authenticity & credibility synthesis", icon: CheckCircle2 },
];

export default function VerificationWorkspace({
  user,
  selectedFile,
  previewUrl,
  aiAnalysisResult,
  analysisError,
  isAnalyzing,
  hasVerified,
  onFileSelect,
  onFileRemove,
  onOpenCamera,
  onStartVerification,
  onCancelVerification,
  onResetVerification,
  onOpenLogin,
  onOpenSignup,
}: VerificationWorkspaceProps) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Honest elapsed seconds timer during analysis (no fake cycling messages)
  useEffect(() => {
    if (!isAnalyzing) {
      setElapsedSeconds(0);
      return;
    }
    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [isAnalyzing]);

  return (
    <section
      id="verification-workspace"
      className="py-16 md:py-24 bg-[#0B0B12] text-[#F8FAFC]"
    >
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Section Heading */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-[#191925] border border-[#303047] text-[#EC4899] text-xs font-semibold uppercase tracking-wider">
            <Sparkle className="w-3.5 h-3.5 text-[#EC4899] fill-[#EC4899]" />
            <span>AI Product Verification</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[#F8FAFC] tracking-tight">
            Verify Your Cosmetic Product
          </h2>
          <p className="text-[#A1A1B5] max-w-xl mx-auto text-base leading-relaxed">
            Upload or capture a photo of your cosmetic product to verify its packaging identity, compare marketplace listings, and inspect customer sentiment.
          </p>
        </div>

        {/* LOGGED-OUT STATE: Dark Callout Card */}
        {!user ? (
          <div className="rounded-3xl p-8 sm:p-12 shadow-2xl border border-[#303047] text-center space-y-6 bg-[#191925]">
            <div className="w-16 h-16 rounded-full bg-[#202033] border border-[#303047] text-[#A855F7] flex items-center justify-center mx-auto shadow-inner">
              <Lock className="w-8 h-8 text-[#A855F7]" />
            </div>

            <div className="space-y-2 max-w-md mx-auto">
              <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 bg-[#202033] text-[#A855F7] rounded-full border border-[#303047]">
                Sign In Required
              </span>
              <h3 className="text-2xl font-bold text-[#F8FAFC] pt-1">
                Access Product Verification
              </h3>
              <p className="text-sm text-[#A1A1B5] leading-relaxed">
                Please sign in or create a free account to upload product photos, scan with your camera, and view marketplace analysis.
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2 max-w-sm mx-auto">
              <button
                type="button"
                onClick={onOpenLogin}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 text-sm font-bold text-white bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-[#8B5CF6] hover:opacity-95 rounded-xl shadow-lg shadow-purple-950/40 touch-manipulation min-h-[44px] cursor-pointer transition-all"
              >
                <LogIn className="w-4 h-4" />
                <span>Sign In to Verify</span>
              </button>

              <button
                type="button"
                onClick={onOpenSignup}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 text-sm font-bold text-[#F8FAFC] bg-[#12121C] hover:bg-[#202033] border border-[#303047] rounded-xl shadow-xs touch-manipulation min-h-[44px] cursor-pointer transition-all"
              >
                <UserPlus className="w-4 h-4 text-[#A855F7]" />
                <span>Create Free Account</span>
              </button>
            </div>
          </div>
        ) : (
          /* LOGGED-IN STATE: Professional Dark Verification Workspace */
          <div className="space-y-6">
            {/* Active Upload Card */}
            <div className="rounded-3xl p-6 sm:p-10 shadow-2xl border border-[#303047] bg-[#191925]">
              <ImageUploader
                selectedFile={selectedFile}
                previewUrl={previewUrl}
                onFileSelect={onFileSelect}
                onFileRemove={onFileRemove}
                onOpenCamera={onOpenCamera}
              />

              {/* Processing Stages Indicator (Displayed honestly during in-flight analysis) */}
              {isAnalyzing && (
                <div className="mt-6 p-5 rounded-2xl bg-[#12121C] border border-[#303047] space-y-4 animate-fadeIn">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <Loader2 className="w-5 h-5 text-[#A855F7] animate-spin" />
                      <span className="text-sm font-bold text-[#F8FAFC]">
                        AI Verification Pipeline Active
                      </span>
                    </div>
                    <span className="text-xs font-mono text-[#A1A1B5] bg-[#202033] px-2.5 py-1 rounded-md border border-[#303047]">
                      {elapsedSeconds}s elapsed
                    </span>
                  </div>

                  <div className="space-y-2">
                    {PROCESSING_STAGES.map((stage, idx) => {
                      const StageIcon = stage.icon;
                      return (
                        <div
                          key={stage.id}
                          className="flex items-center gap-3 text-xs text-[#A1A1B5] py-1 px-2 rounded-lg bg-[#191925]/60"
                        >
                          <StageIcon className="w-3.5 h-3.5 text-[#A855F7] shrink-0" />
                          <span className="font-medium text-[#F8FAFC]/90">
                            Stage {idx + 1}:
                          </span>
                          <span className="truncate">{stage.label}</span>
                        </div>
                      );
                    })}
                  </div>

                  {onCancelVerification && (
                    <div className="pt-2 flex justify-end">
                      <button
                        type="button"
                        onClick={onCancelVerification}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-[#F87171] hover:bg-[#F87171]/10 border border-[#F87171]/30 transition-colors cursor-pointer"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Cancel Request</span>
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Action Footer */}
              <div className="mt-8 pt-6 border-t border-[#303047] flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-2 text-xs text-[#A1A1B5] font-medium">
                  <ShieldCheck className="w-4 h-4 text-[#A855F7] shrink-0" />
                  <span>JPG, PNG, WEBP • Max 15 MB • Auto-optimized</span>
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto">
                  {isAnalyzing && onCancelVerification && (
                    <button
                      type="button"
                      onClick={onCancelVerification}
                      className="inline-flex items-center justify-center gap-1.5 px-4 py-3.5 text-sm font-semibold text-[#F87171] bg-[#12121C] hover:bg-[#202033] border border-[#F87171]/30 rounded-xl transition-all cursor-pointer"
                    >
                      <span>Cancel</span>
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={onStartVerification}
                    disabled={isAnalyzing}
                    className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2.5 px-8 py-4 text-base font-bold text-white bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-[#8B5CF6] hover:opacity-95 disabled:opacity-60 rounded-2xl shadow-lg shadow-purple-900/30 active:scale-95 transition-all duration-200 touch-manipulation min-h-[48px] cursor-pointer"
                  >
                    {isAnalyzing ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <span>Processing Image...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-5 h-5 text-pink-200" />
                        <span>Verify Product</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Error & Non-Cosmetic Rejection Banner */}
            {analysisError && (
              <div className="p-4 bg-[#202033] border border-[#F87171]/40 rounded-2xl text-[#F8FAFC] text-xs sm:text-sm flex items-start gap-3 shadow-lg animate-fadeIn">
                <AlertCircle className="w-5 h-5 text-[#F87171] shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="font-bold text-[#F87171]">
                    {analysisError.includes("Non-cosmetic") ? "Non-Cosmetic Image Detected" : "Verification Could Not Be Completed"}
                  </h4>
                  <p className="text-[#F8FAFC] text-sm font-semibold">
                    {analysisError}
                  </p>
                  <p className="text-[11px] text-[#A1A1B5] pt-0.5 leading-relaxed">
                    {analysisError.includes("Non-cosmetic")
                      ? "CosmeticVerify only inspects cosmetic and beauty products (makeup, skincare, beauty packaging). Please upload a valid cosmetic product photo."
                      : "Please ensure the image is clear and try again in a moment."}
                  </p>
                </div>
              </div>
            )}

            {/* Verification Results Container */}
            {hasVerified && (
              <div id="verification-results-container" className="pt-4">
                <VerificationResult
                  previewUrl={previewUrl}
                  aiAnalysisResult={aiAnalysisResult}
                  onReset={onResetVerification}
                />
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
