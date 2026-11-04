"use client";

import { useState, FormEvent, useEffect } from "react";
import { X, Mail, ShieldCheck, ArrowLeft, Loader2 } from "lucide-react";
import { toast } from "react-toastify";

interface ForgotPasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
  onBackToLogin: () => void;
}

export default function ForgotPasswordModal({ isOpen, onClose, onBackToLogin }: ForgotPasswordModalProps) {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [emailError, setEmailError] = useState<string | null>(null);

  // Lock background body scroll when open
  useEffect(() => {
    if (isOpen) {
      document.body.classList.add("overflow-hidden");
    } else {
      document.body.classList.remove("overflow-hidden");
    }
    return () => {
      document.body.classList.remove("overflow-hidden");
    };
  }, [isOpen]);

  // Keyboard escape listener to close modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const validateEmail = (val: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val);
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    setEmailError(null);

    const trimmed = email.trim();
    if (!trimmed) {
      setEmailError("Email address is required.");
      return;
    }
    if (!validateEmail(trimmed)) {
      setEmailError("Please enter a valid email address.");
      return;
    }

    setIsLoading(true);

    setTimeout(() => {
      setIsLoading(false);
      toast.success("Demo reset link generated. Real email service will be connected later.", {
        toastId: "forgot-password-success",
      });
      setEmail("");
      onBackToLogin();
    }, 1000);
  };

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-3 sm:p-4 bg-[#0B0B12]/80 backdrop-blur-md overflow-y-auto animate-fadeIn pointer-events-auto modal-scroll-container"
      role="dialog"
      aria-modal="true"
      aria-labelledby="forgot-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="relative w-full bg-[#191925] rounded-3xl shadow-2xl border border-[#303047] overflow-hidden my-auto text-[#F8FAFC] focus:outline-none z-[210] pointer-events-auto"
        style={{ width: "min(100% - 24px, 460px)", maxHeight: "calc(100dvh - 24px)" }}
      >
        {/* Modal Header */}
        <div className="bg-gradient-to-r from-[#12121C] via-[#191925] to-[#202033] border-b border-[#303047] text-[#F8FAFC] p-5 sm:p-7 relative shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="absolute top-4 right-4 text-[#A1A1B5] hover:text-[#F8FAFC] bg-[#202033] hover:bg-[#303047] p-2.5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[#A855F7] touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer z-10"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2.5 mb-2">
            <div className="w-9 h-9 rounded-xl bg-[#EC4899]/15 border border-[#EC4899]/30 flex items-center justify-center text-[#EC4899]">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <span className="text-xl font-bold text-[#F8FAFC] tracking-tight">
              Cosmetic<span className="text-[#EC4899]">Verify</span>
            </span>
          </div>

          <h2 id="forgot-modal-title" className="text-xl sm:text-2xl font-extrabold text-[#F8FAFC] mt-1">
            Reset Password
          </h2>
          <p className="text-xs text-[#A1A1B5] mt-1 leading-relaxed">
            Enter your email address and we will generate a password reset link.
          </p>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit} className="p-5 sm:p-7 space-y-5 overflow-y-auto" style={{ maxHeight: "calc(100dvh - 140px)" }}>
          {/* Email Input */}
          <div className="space-y-1.5">
            <label htmlFor="forgot-email" className="block text-xs font-bold text-[#A1A1B5] uppercase tracking-wider">
              Email Address
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#A1A1B5]/60">
                <Mail className="w-4 h-4" />
              </div>
              <input
                id="forgot-email"
                type="email"
                autoComplete="email"
                inputMode="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (emailError) setEmailError(null);
                }}
                placeholder="name@example.com"
                className={`w-full pl-10 pr-4 py-3 bg-[#12121C] border ${
                  emailError ? "border-[#F87171] bg-[#F87171]/10" : "border-[#303047]"
                } rounded-xl text-[#F8FAFC] placeholder-[#A1A1B5]/40 text-sm sm:text-base focus:outline-none focus:ring-1 focus:ring-[#A855F7] focus:border-[#A855F7] transition-all`}
                aria-invalid={!!emailError}
                aria-describedby={emailError ? "forgot-email-error" : undefined}
                required
              />
            </div>
            {emailError && (
              <p id="forgot-email-error" className="text-xs text-[#F87171] font-medium">
                {emailError}
              </p>
            )}
          </div>

          {/* Submit Action */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3.5 px-4 text-sm font-bold text-white bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-[#8B5CF6] hover:opacity-95 disabled:opacity-60 rounded-xl shadow-lg shadow-purple-950/40 min-h-[44px] touch-manipulation flex items-center justify-center gap-2 transition-all cursor-pointer"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Sending Reset Link...</span>
              </>
            ) : (
              <span>Send Reset Link</span>
            )}
          </button>

          {/* Back to Login */}
          <div className="text-center pt-3 border-t border-[#303047]">
            <button
              type="button"
              onClick={onBackToLogin}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-[#EC4899] hover:underline min-h-[44px] touch-manipulation cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4 text-[#A855F7]" />
              <span>Back to Sign In</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
