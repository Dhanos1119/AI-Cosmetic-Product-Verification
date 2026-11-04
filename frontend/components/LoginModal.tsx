"use client";

/* 
 * NOTE: Demo authentication only. Replace with backend authentication later.
 */

import { useState, FormEvent, useEffect } from "react";
import { X, Eye, EyeOff, Lock, Mail, ShieldCheck, KeyRound, Loader2 } from "lucide-react";
import { toast } from "react-toastify";

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLoginSuccess: (user: { email: string; name: string }) => void;
  onSwitchToSignup: () => void;
  onSwitchToForgot: () => void;
}

export default function LoginModal({
  isOpen,
  onClose,
  onLoginSuccess,
  onSwitchToSignup,
  onSwitchToForgot,
}: LoginModalProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Field validation state
  const [emailError, setEmailError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  // Lock background body scroll when modal is open
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

  const handleFillDemo = () => {
    setEmail("demo@example.com");
    setPassword("Demo@123");
    setEmailError(null);
    setPasswordError(null);
    toast.info("Demo credentials filled: demo@example.com", {
      toastId: "fill-demo-info",
    });
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (isLoading) return; // Prevent duplicate submissions

    setEmailError(null);
    setPasswordError(null);

    let hasError = false;
    const trimmedEmail = email.trim();

    if (!trimmedEmail) {
      setEmailError("Email address is required.");
      hasError = true;
    } else if (!validateEmail(trimmedEmail)) {
      setEmailError("Please enter a valid email address.");
      hasError = true;
    }

    if (!password) {
      setPasswordError("Password is required.");
      hasError = true;
    }

    if (hasError) {
      toast.error("Please fill in all required login fields correctly.", {
        toastId: "login-validation-error",
      });
      return;
    }

    setIsLoading(true);

    try {
      const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
      const loginUrl = process.env.NEXT_PUBLIC_LOGIN_URL || `http://${host}:5000/api/auth/login`;

      const res = await fetch(loginUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: trimmedEmail.toLowerCase(),
          password,
        }),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        setIsLoading(false);
        toast.error("Invalid email or password.", {
          toastId: "login-invalid-toast",
        });
        return;
      }

      // Store authenticated session
      if (typeof window !== "undefined") {
        if (data.token) {
          localStorage.setItem("cosmetic_verify_token", data.token);
        }
        if (data.user) {
          localStorage.setItem("cosmetic_verify_user", JSON.stringify(data.user));
        }
      }

      setIsLoading(false);
      toast.success("Login successful!", {
        toastId: "login-success-toast",
      });

      onLoginSuccess(data.user || { email: trimmedEmail.toLowerCase(), name: "User" });
      onClose();
    } catch (err) {
      console.error("Login request error:", err);
      setIsLoading(false);
      toast.error("Invalid email or password.", {
        toastId: "login-invalid-toast",
      });
    }
  };

  const handleSocialClick = (provider: string) => {
    toast.info(`${provider} login is demo-only. Use demo credentials above.`, {
      toastId: `social-${provider}`,
    });
  };

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-3 sm:p-4 bg-[#0B0B12]/80 backdrop-blur-md overflow-y-auto animate-fadeIn pointer-events-auto modal-scroll-container"
      role="dialog"
      aria-modal="true"
      aria-labelledby="login-modal-title"
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
            aria-label="Close login modal"
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

          <h2 id="login-modal-title" className="text-xl sm:text-2xl font-extrabold text-[#F8FAFC] mt-1">
            Welcome Back
          </h2>
          <p className="text-xs text-[#A1A1B5] mt-1 leading-relaxed">
            Sign in to continue to your cosmetic verification dashboard.
          </p>
        </div>

        {/* Modal Form */}
        <form
          onSubmit={handleSubmit}
          className="p-5 sm:p-7 space-y-4 overflow-y-auto modal-scroll-container"
          style={{ maxHeight: "calc(100dvh - 140px)" }}
        >
          {/* Dev-only helper box */}
          <div className="p-3 bg-[#12121C] border border-[#303047] rounded-2xl flex items-center justify-between text-xs text-[#A1A1B5]">
            <div className="space-y-0.5">
              <span className="font-bold flex items-center gap-1 text-[#F8FAFC]">
                <KeyRound className="w-3.5 h-3.5 text-[#A855F7]" />
                <span>Dev Demo Credentials:</span>
              </span>
              <p className="text-[11px] text-[#A1A1B5]">demo@example.com | Demo@123</p>
            </div>
            <button
              type="button"
              onClick={handleFillDemo}
              className="px-3 py-1.5 bg-[#A855F7] hover:bg-[#9333EA] text-white font-bold text-xs rounded-xl shadow-xs transition-colors shrink-0 touch-manipulation min-h-[38px] cursor-pointer"
            >
              Fill Demo
            </button>
          </div>

          {/* Email Address Input */}
          <div className="space-y-1">
            <label htmlFor="official-login-email" className="block text-xs font-bold text-[#A1A1B5] uppercase tracking-wider">
              Email Address
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#A1A1B5]/60">
                <Mail className="w-4 h-4" />
              </div>
              <input
                id="official-login-email"
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
                aria-describedby={emailError ? "login-email-error" : undefined}
                required
              />
            </div>
            {emailError && (
              <p id="login-email-error" className="text-xs text-[#F87171] font-medium">
                {emailError}
              </p>
            )}
          </div>

          {/* Password Input */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label htmlFor="official-login-password" className="block text-xs font-bold text-[#A1A1B5] uppercase tracking-wider">
                Password
              </label>
              <button
                type="button"
                onClick={onSwitchToForgot}
                className="text-xs font-semibold text-[#A855F7] hover:text-pink-400 hover:underline touch-manipulation min-h-[38px] flex items-center cursor-pointer"
              >
                Forgot password?
              </button>
            </div>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-[#A1A1B5]/60">
                <Lock className="w-4 h-4" />
              </div>
              <input
                id="official-login-password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (passwordError) setPasswordError(null);
                }}
                placeholder="••••••••"
                className={`w-full pl-10 pr-11 py-3 bg-[#12121C] border ${
                  passwordError ? "border-[#F87171] bg-[#F87171]/10" : "border-[#303047]"
                } rounded-xl text-[#F8FAFC] placeholder-[#A1A1B5]/40 text-sm sm:text-base focus:outline-none focus:ring-1 focus:ring-[#A855F7] focus:border-[#A855F7] transition-all`}
                aria-invalid={!!passwordError}
                aria-describedby={passwordError ? "login-password-error" : undefined}
                required
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
            {passwordError && (
              <p id="login-password-error" className="text-xs text-[#F87171] font-medium">
                {passwordError}
              </p>
            )}
          </div>

          {/* Remember Me Checkbox */}
          <div className="flex items-center">
            <label className="flex items-center gap-2.5 cursor-pointer text-xs font-medium text-[#A1A1B5] touch-manipulation">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 rounded border-[#303047] bg-[#12121C] text-[#A855F7] focus:ring-[#A855F7] touch-manipulation cursor-pointer"
              />
              <span>Remember me on this device</span>
            </label>
          </div>

          {/* Login Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3.5 px-4 text-sm font-bold text-white bg-gradient-to-r from-[#EC4899] via-[#A855F7] to-[#8B5CF6] hover:opacity-95 disabled:opacity-60 rounded-xl shadow-lg shadow-purple-950/40 min-h-[44px] touch-manipulation flex items-center justify-center gap-2 transition-all cursor-pointer mt-1"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Signing In...</span>
              </>
            ) : (
              <span>Sign In</span>
            )}
          </button>

          {/* Social Divider */}
          <div className="relative my-3 text-center">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-[#303047]" />
            </div>
            <span className="relative bg-[#191925] px-3 text-xs uppercase font-semibold text-[#A1A1B5]">
              or
            </span>
          </div>

          {/* Optional Demo Social Logins */}
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => handleSocialClick("Google")}
              className="py-2.5 px-3 bg-[#12121C] hover:bg-[#202033] border border-[#303047] rounded-xl text-xs font-semibold text-[#F8FAFC] flex items-center justify-center gap-2 touch-manipulation min-h-[44px] cursor-pointer transition-colors"
            >
              <span>Google (Demo)</span>
            </button>
            <button
              type="button"
              onClick={() => handleSocialClick("Apple")}
              className="py-2.5 px-3 bg-[#12121C] hover:bg-[#202033] border border-[#303047] rounded-xl text-xs font-semibold text-[#F8FAFC] flex items-center justify-center gap-2 touch-manipulation min-h-[44px] cursor-pointer transition-colors"
            >
              <span>Apple (Demo)</span>
            </button>
          </div>

          {/* Create Account Section */}
          <div className="text-center pt-3 border-t border-[#303047]">
            <p className="text-xs text-[#A1A1B5]">
              New to CosmeticVerify?{" "}
              <button
                type="button"
                onClick={onSwitchToSignup}
                className="font-bold text-[#EC4899] hover:underline min-h-[44px] inline-flex items-center touch-manipulation cursor-pointer"
              >
                Create an account
              </button>
            </p>
          </div>
        </form>
      </div>
    </div>
  );
}
