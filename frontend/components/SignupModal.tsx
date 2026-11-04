"use client";

/* 
 * NOTE: Demo authentication only. Replace with backend authentication later.
 */

import { useState, FormEvent, useEffect } from "react";
import { X, Eye, EyeOff, Lock, Mail, User, ShieldCheck, Loader2 } from "lucide-react";
import { toast } from "react-toastify";

interface SignupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSwitchToLogin: () => void;
}

export default function SignupModal({ isOpen, onClose, onSwitchToLogin }: SignupModalProps) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Field validation errors
  const [errors, setErrors] = useState<{
    fullName?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
    terms?: string;
  }>({});

  // Body scroll lock on mobile/desktop when modal is open
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

  // Keyboard escape handler
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

  // Password strength calculation
  const getPasswordStrength = (pass: string) => {
    if (!pass) return { score: 0, label: "None", color: "bg-[#202033]" };
    let score = 0;
    if (pass.length >= 8) score += 1;
    if (/[A-Z]/.test(pass)) score += 1;
    if (/[a-z]/.test(pass)) score += 1;
    if (/[0-9]/.test(pass)) score += 1;
    if (/[^A-Za-z0-9]/.test(pass)) score += 1;

    if (score <= 2) return { score: 33, label: "Weak", color: "bg-[#F87171]" };
    if (score <= 4) return { score: 66, label: "Medium", color: "bg-[#F59E0B]" };
    return { score: 100, label: "Strong", color: "bg-[#22C55E]" };
  };

  const strength = getPasswordStrength(password);

  const validate = () => {
    const newErrors: typeof errors = {};

    if (!fullName.trim()) {
      newErrors.fullName = "Full name is required.";
    }

    const emailTrimmed = email.trim();
    if (!emailTrimmed) {
      newErrors.email = "Email address is required.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailTrimmed)) {
      newErrors.email = "Please enter a valid email address.";
    }

    if (!password) {
      newErrors.password = "Password is required.";
    } else {
      if (password.length < 8) {
        newErrors.password = "Password must be at least 8 characters.";
      } else if (!/[A-Z]/.test(password)) {
        newErrors.password = "Password must contain at least one uppercase letter.";
      } else if (!/[a-z]/.test(password)) {
        newErrors.password = "Password must contain at least one lowercase letter.";
      } else if (!/[0-9]/.test(password)) {
        newErrors.password = "Password must contain at least one number.";
      }
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password.";
    } else if (confirmPassword !== password) {
      newErrors.confirmPassword = "Passwords do not match.";
    }

    if (!termsAccepted) {
      newErrors.terms = "You must agree to the Terms of Service & Privacy Policy.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (isLoading) return; // Prevent duplicate submissions

    if (!validate()) {
      toast.error("Please correct the highlighted form errors.", {
        toastId: "signup-form-errors",
      });
      return;
    }

    setIsLoading(true);

    try {
      const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
      const signupUrl = process.env.NEXT_PUBLIC_SIGNUP_URL || `http://${host}:5000/api/auth/signup`;

      const res = await fetch(signupUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          fullName: fullName.trim(),
          email: email.trim().toLowerCase(),
          password,
        }),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        setIsLoading(false);
        const errorMsg = data.message || "Failed to create account. Please try again.";
        toast.error(errorMsg, {
          toastId: "signup-error-toast",
        });
        return;
      }

      setIsLoading(false);
      toast.success("Account created successfully! Please sign in.", {
        toastId: "signup-success-toast",
      });
      onSwitchToLogin();
    } catch (err: any) {
      console.error("Signup request error:", err);
      setIsLoading(false);
      toast.error("Unable to complete registration. Please check your connection.", {
        toastId: "signup-network-error",
      });
    }
  };

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-3 sm:p-4 bg-[#0B0B12]/80 backdrop-blur-md overflow-y-auto animate-fadeIn pointer-events-auto modal-scroll-container"
      role="dialog"
      aria-modal="true"
      aria-labelledby="signup-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="relative w-full bg-[#191925] rounded-3xl shadow-2xl border border-[#303047] overflow-hidden my-auto text-[#F8FAFC] focus:outline-none z-[210] pointer-events-auto"
        style={{ width: "min(100% - 24px, 480px)", maxHeight: "calc(100dvh - 24px)" }}
      >
        {/* Modal Header */}
        <div className="bg-gradient-to-r from-[#12121C] via-[#191925] to-[#202033] border-b border-[#303047] text-[#F8FAFC] p-5 sm:p-7 relative shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="absolute top-4 right-4 text-[#A1A1B5] hover:text-[#F8FAFC] bg-[#202033] hover:bg-[#303047] p-2.5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-[#A855F7] touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer z-10"
            aria-label="Close registration modal"
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

          <h2 id="signup-modal-title" className="text-xl sm:text-2xl font-extrabold text-[#F8FAFC] mt-1">
            Create an Account
          </h2>
          <p className="text-xs text-[#A1A1B5] mt-1">
            Join CosmeticVerify to access product verification services.
          </p>
        </div>

        {/* Modal Form */}
        <form
          onSubmit={handleSubmit}
          className="p-5 sm:p-7 space-y-4 overflow-y-auto modal-scroll-container"
          style={{ maxHeight: "calc(100dvh - 140px)" }}
        >
          {/* Full Name */}
          <div className="space-y-1">
            <label htmlFor="signup-name" className="block text-xs font-bold text-[#A1A1B5] uppercase tracking-wider">
              Full Name
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#A1A1B5]/60">
                <User className="w-4 h-4" />
              </div>
              <input
                id="signup-name"
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Jane Doe"
                className={`w-full pl-10 pr-4 py-3 bg-[#12121C] border ${
                  errors.fullName ? "border-[#F87171] bg-[#F87171]/10" : "border-[#303047]"
                } rounded-xl text-[#F8FAFC] placeholder-[#A1A1B5]/40 text-sm sm:text-base focus:outline-none focus:ring-1 focus:ring-[#A855F7] focus:border-[#A855F7] transition-all`}
                aria-invalid={!!errors.fullName}
              />
            </div>
            {errors.fullName && <p className="text-xs text-[#F87171] font-medium">{errors.fullName}</p>}
          </div>

          {/* Email Address */}
          <div className="space-y-1">
            <label htmlFor="signup-email" className="block text-xs font-bold text-[#A1A1B5] uppercase tracking-wider">
              Email Address
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#A1A1B5]/60">
                <Mail className="w-4 h-4" />
              </div>
              <input
                id="signup-email"
                type="email"
                autoComplete="email"
                inputMode="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className={`w-full pl-10 pr-4 py-3 bg-[#12121C] border ${
                  errors.email ? "border-[#F87171] bg-[#F87171]/10" : "border-[#303047]"
                } rounded-xl text-[#F8FAFC] placeholder-[#A1A1B5]/40 text-sm sm:text-base focus:outline-none focus:ring-1 focus:ring-[#A855F7] focus:border-[#A855F7] transition-all`}
                aria-invalid={!!errors.email}
              />
            </div>
            {errors.email && <p className="text-xs text-[#F87171] font-medium">{errors.email}</p>}
          </div>

          {/* Password */}
          <div className="space-y-1">
            <label htmlFor="signup-password" className="block text-xs font-bold text-[#A1A1B5] uppercase tracking-wider">
              Password
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#A1A1B5]/60">
                <Lock className="w-4 h-4" />
              </div>
              <input
                id="signup-password"
                type={showPassword ? "text" : "password"}
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className={`w-full pl-10 pr-11 py-3 bg-[#12121C] border ${
                  errors.password ? "border-[#F87171] bg-[#F87171]/10" : "border-[#303047]"
                } rounded-xl text-[#F8FAFC] placeholder-[#A1A1B5]/40 text-sm sm:text-base focus:outline-none focus:ring-1 focus:ring-[#A855F7] focus:border-[#A855F7] transition-all`}
                aria-invalid={!!errors.password}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-[#A1A1B5] hover:text-[#F8FAFC] touch-manipulation min-h-[44px] min-w-[44px] justify-center cursor-pointer"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.password && <p className="text-xs text-[#F87171] font-medium">{errors.password}</p>}

            {/* Password Strength Indicator */}
            {password && (
              <div className="pt-1.5 space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#A1A1B5]">Password Strength:</span>
                  <span className="font-bold text-[#F8FAFC]">{strength.label}</span>
                </div>
                <div className="w-full h-1.5 bg-[#202033] rounded-full overflow-hidden">
                  <div
                    className={`h-full ${strength.color} transition-all duration-300`}
                    style={{ width: `${strength.score}%` }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Confirm Password */}
          <div className="space-y-1">
            <label htmlFor="signup-confirm-password" className="block text-xs font-bold text-[#A1A1B5] uppercase tracking-wider">
              Confirm Password
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#A1A1B5]/60">
                <Lock className="w-4 h-4" />
              </div>
              <input
                id="signup-confirm-password"
                type={showConfirmPassword ? "text" : "password"}
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••"
                className={`w-full pl-10 pr-11 py-3 bg-[#12121C] border ${
                  errors.confirmPassword ? "border-[#F87171] bg-[#F87171]/10" : "border-[#303047]"
                } rounded-xl text-[#F8FAFC] placeholder-[#A1A1B5]/40 text-sm sm:text-base focus:outline-none focus:ring-1 focus:ring-[#A855F7] focus:border-[#A855F7] transition-all`}
                aria-invalid={!!errors.confirmPassword}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-[#A1A1B5] hover:text-[#F8FAFC] touch-manipulation min-h-[44px] min-w-[44px] justify-center cursor-pointer"
                aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
              >
                {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {errors.confirmPassword && (
              <p className="text-xs text-[#F87171] font-medium">{errors.confirmPassword}</p>
            )}
          </div>

          {/* Terms & Conditions Checkbox */}
          <div className="pt-1">
            <label className="flex items-start gap-2.5 cursor-pointer text-xs text-[#A1A1B5] touch-manipulation">
              <input
                type="checkbox"
                checked={termsAccepted}
                onChange={(e) => setTermsAccepted(e.target.checked)}
                className="mt-0.5 w-4 h-4 rounded border-[#303047] bg-[#12121C] text-[#A855F7] focus:ring-[#A855F7] touch-manipulation cursor-pointer"
              />
              <span className="leading-snug">
                I agree to the <span className="font-semibold text-[#EC4899]">Terms of Service</span> and{" "}
                <span className="font-semibold text-[#EC4899]">Privacy Policy</span>.
              </span>
            </label>
            {errors.terms && <p className="text-xs text-[#F87171] font-medium mt-1">{errors.terms}</p>}
          </div>

          {/* Submit Action */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3.5 px-4 text-sm font-bold text-white bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-[#8B5CF6] hover:opacity-95 disabled:opacity-60 rounded-xl shadow-lg shadow-purple-950/40 min-h-[44px] touch-manipulation flex items-center justify-center gap-2 transition-all cursor-pointer mt-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Creating Account...</span>
              </>
            ) : (
              <span>Create Account</span>
            )}
          </button>

          {/* Switch to Login Link */}
          <div className="text-center pt-3 border-t border-[#303047]">
            <p className="text-xs text-[#A1A1B5]">
              Already have an account?{" "}
              <button
                type="button"
                onClick={onSwitchToLogin}
                className="font-bold text-[#EC4899] hover:underline min-h-[44px] inline-flex items-center touch-manipulation cursor-pointer"
              >
                Sign In
              </button>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
