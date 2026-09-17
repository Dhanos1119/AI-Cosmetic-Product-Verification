"use client";

import { Lock, LogIn, UserPlus, Camera, ShieldCheck, Sparkles, Loader2, Info, CheckCircle2 } from "lucide-react";
import ImageUploader from "./ImageUploader";
import VerificationResult, { AiAnalysisResult } from "./VerificationResult";

interface VerificationWorkspaceProps {
  user: { email: string; name: string } | null;
  selectedFile: File | null;
  previewUrl: string | null;
  aiAnalysisResult: AiAnalysisResult | null;
  isAnalyzing: boolean;
  hasVerified: boolean;
  onFileSelect: (file: File) => void;
  onFileRemove: () => void;
  onOpenCamera: () => void;
  onStartVerification: (e?: React.MouseEvent) => void;
  onResetVerification: () => void;
  onOpenLogin: () => void;
  onOpenSignup: () => void;
}

export default function VerificationWorkspace({
  user,
  selectedFile,
  previewUrl,
  aiAnalysisResult,
  isAnalyzing,
  hasVerified,
  onFileSelect,
  onFileRemove,
  onOpenCamera,
  onStartVerification,
  onResetVerification,
  onOpenLogin,
  onOpenSignup,
}: VerificationWorkspaceProps) {
  return (
    <section
      id="verification-workspace"
      className="py-16 md:py-24 bg-gradient-to-b from-transparent via-purple-50/40 to-transparent"
    >
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Section Heading */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-purple-100/90 border border-purple-200 text-purple-950 text-xs font-semibold uppercase tracking-wider">
            <Camera className="w-3.5 h-3.5 text-purple-700" />
            <span>Cosmetic Verification Workspace</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            Product Verification Workspace
          </h2>
          <p className="text-slate-600 max-w-xl mx-auto text-base">
            Upload or capture a cosmetic container photo to perform identity verification and marketplace trust analysis.
          </p>
        </div>

        {/* LOGGED-OUT STATE: Locked Overlay Callout Card */}
        {!user ? (
          <div className="glass-card rounded-3xl p-8 sm:p-12 shadow-xl shadow-purple-900/5 border border-purple-200 text-center space-y-6">
            <div className="w-16 h-16 rounded-full bg-purple-100 border border-purple-200 text-purple-700 flex items-center justify-center mx-auto shadow-inner">
              <Lock className="w-8 h-8 text-purple-600" />
            </div>

            <div className="space-y-2 max-w-md mx-auto">
              <span className="text-xs font-bold uppercase tracking-wider px-3 py-1 bg-purple-100 text-purple-900 rounded-full border border-purple-200">
                Sign In Required
              </span>
              <h3 className="text-2xl font-bold text-slate-900 pt-1">
                Access Cosmetic Verification
              </h3>
              <p className="text-sm text-slate-600 leading-relaxed">
                Please sign in or create an account to upload product images, use camera scanning, and run authenticity checks.
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2 max-w-sm mx-auto">
              <button
                type="button"
                onClick={onOpenLogin}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 text-sm font-bold text-white bg-gradient-to-r from-pink-500 via-purple-600 to-indigo-600 hover:opacity-95 rounded-xl shadow-md touch-manipulation min-h-[44px] cursor-pointer"
              >
                <LogIn className="w-4 h-4" />
                <span>Sign In to Access Workspace</span>
              </button>

              <button
                type="button"
                onClick={onOpenSignup}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 text-sm font-bold text-purple-950 bg-white hover:bg-purple-50 border border-purple-200 rounded-xl shadow-2xs touch-manipulation min-h-[44px] cursor-pointer"
              >
                <UserPlus className="w-4 h-4 text-purple-600" />
                <span>Create Account</span>
              </button>
            </div>

            {/* Blurred Mock Preview Box */}
            <div className="pt-6 border-t border-purple-100 pointer-events-none opacity-50 select-none">
              <div className="p-6 border-2 border-dashed border-purple-200 rounded-2xl bg-slate-50 flex items-center justify-center gap-2 text-xs text-slate-400">
                <ShieldCheck className="w-5 h-5 text-purple-400" />
                <span>Image uploader & camera scanner locked until authenticated</span>
              </div>
            </div>
          </div>
        ) : (
          /* LOGGED-IN STATE: Active Workspace Container */
          <div className="space-y-6">
            {/* Logged-In User Banner */}
            <div className="p-4 bg-gradient-to-r from-purple-900 via-indigo-900 to-slate-900 text-white rounded-2xl shadow-md flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-pink-500/20 border border-pink-400/30 flex items-center justify-center text-pink-300 font-bold shrink-0">
                  {user.name ? user.name[0].toUpperCase() : "D"}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-white">{user.name || "Demo User"}</span>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-300 bg-emerald-950 px-2 py-0.5 rounded-md border border-emerald-700/60 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      <span>Workspace Ready</span>
                    </span>
                  </div>
                  <p className="text-xs text-purple-200">{user.email}</p>
                </div>
              </div>

              <div className="text-xs text-pink-200 bg-purple-950/60 px-3 py-1.5 rounded-xl border border-purple-800/80">
                Demo Auth Mode Active
              </div>
            </div>

            {/* Active Upload Card */}
            <div className="glass-card rounded-3xl p-6 sm:p-10 shadow-xl shadow-purple-900/5 border border-purple-150">
              <ImageUploader
                selectedFile={selectedFile}
                previewUrl={previewUrl}
                onFileSelect={onFileSelect}
                onFileRemove={onFileRemove}
                onOpenCamera={onOpenCamera}
              />

              {/* Start Verification Action Button */}
              <div className="mt-8 pt-6 border-t border-purple-100 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
                  <ShieldCheck className="w-4 h-4 text-purple-600 shrink-0" />
                  <span>JPG, JPEG, PNG, WEBP • Max 10 MB</span>
                </div>

                <button
                  type="button"
                  onClick={onStartVerification}
                  disabled={isAnalyzing}
                  className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-4 text-base font-bold text-white bg-gradient-to-r from-pink-500 via-purple-600 to-indigo-600 hover:opacity-95 disabled:opacity-60 rounded-2xl shadow-lg shadow-purple-500/20 active:scale-95 transition-all duration-200 touch-manipulation min-h-[48px] cursor-pointer"
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      <span>Sending to AI Service (Port 8001)...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5 text-pink-200" />
                      <span>Start AI Verification</span>
                    </>
                  )}
                </button>
              </div>

              {/* Model Integration Notice */}
              <div className="mt-4 p-3 bg-purple-50/80 rounded-xl text-xs text-purple-900 flex items-center gap-2">
                <Info className="w-4 h-4 text-purple-600 shrink-0" />
                <span>Note: Image is sent directly to FastAPI AI service at port 8001. Image dimensions & integrity are inspected in real time.</span>
              </div>
            </div>

            {/* Verification Results Display Container */}
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
