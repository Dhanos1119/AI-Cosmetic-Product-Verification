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

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
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

    setTimeout(() => {
      setIsLoading(false);
      // Demo credential check
      if (trimmedEmail.toLowerCase() === "demo@example.com" && password === "Demo@123") {
        toast.success("Signed in successfully.", {
          toastId: "login-success-toast",
        });
        onLoginSuccess({
          email: "demo@example.com",
          name: "Demo User",
        });
        onClose();
      } else {
        toast.error("Invalid email or password.", {
          toastId: "login-invalid-toast",
        });
      }
    }, 1000);
  };

  const handleSocialClick = (provider: string) => {
    toast.info(`${provider} login is demo-only. Use demo credentials above.`, {
      toastId: `social-${provider}`,
    });
  };

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-3 sm:p-4 bg-slate-900/70 backdrop-blur-md overflow-y-auto animate-fadeIn pointer-events-auto modal-scroll-container"
      role="dialog"
      aria-modal="true"
      aria-labelledby="login-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="relative w-full bg-white rounded-3xl shadow-2xl border border-purple-100 overflow-hidden my-auto text-slate-900 focus:outline-none z-[210] pointer-events-auto"
        style={{ width: "min(100% - 24px, 480px)", maxHeight: "calc(100dvh - 24px)" }}
      >
        {/* Modal Header */}
        <div className="bg-gradient-to-r from-purple-950 via-purple-900 to-indigo-950 text-white p-5 sm:p-7 relative shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="absolute top-4 right-4 text-purple-200 hover:text-white bg-white/10 hover:bg-white/20 p-2.5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-pink-400 touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer z-10"
            aria-label="Close login modal"
          >
            <X className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2.5 mb-2">
            <div className="w-9 h-9 rounded-xl bg-pink-500/20 border border-pink-400/30 flex items-center justify-center text-pink-300">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <span className="text-xl font-bold text-white tracking-tight">
              Cosmetic<span className="text-pink-400">Verify</span>
            </span>
          </div>

          <h2 id="login-modal-title" className="text-xl sm:text-2xl font-extrabold text-white mt-1">
            Welcome Back
          </h2>
          <p className="text-xs text-purple-200 mt-1 leading-relaxed">
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
          <div className="p-3 bg-purple-50/80 border border-purple-200 rounded-2xl flex items-center justify-between text-xs text-purple-950">
            <div className="space-y-0.5">
              <span className="font-bold flex items-center gap-1">
                <KeyRound className="w-3.5 h-3.5 text-purple-600" />
                <span>Dev Demo Credentials:</span>
              </span>
              <p className="text-[11px] text-purple-700">demo@example.com | Demo@123</p>
            </div>
            <button
              type="button"
              onClick={handleFillDemo}
              className="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs rounded-xl shadow-xs transition-colors shrink-0 touch-manipulation min-h-[38px] cursor-pointer"
            >
              Fill Demo
            </button>
          </div>

          {/* Email Address Input */}
          <div className="space-y-1">
            <label htmlFor="official-login-email" className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
              Email Address
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
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
                className={`w-full pl-10 pr-4 py-3 bg-slate-50 border ${
                  emailError ? "border-rose-500 bg-rose-50/40" : "border-slate-200"
                } rounded-xl text-slate-900 text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white transition-all`}
                aria-invalid={!!emailError}
                aria-describedby={emailError ? "login-email-error" : undefined}
                required
              />
            </div>
            {emailError && (
              <p id="login-email-error" className="text-xs text-rose-600 font-medium">
                {emailError}
              </p>
            )}
          </div>

          {/* Password Input */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label htmlFor="official-login-password" className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Password
              </label>
              <button
                type="button"
                onClick={onSwitchToForgot}
                className="text-xs font-semibold text-purple-700 hover:text-purple-900 hover:underline touch-manipulation min-h-[38px] flex items-center cursor-pointer"
              >
                Forgot password?
              </button>
            </div>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
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
                className={`w-full pl-10 pr-11 py-3 bg-slate-50 border ${
                  passwordError ? "border-rose-500 bg-rose-50/40" : "border-slate-200"
                } rounded-xl text-slate-900 text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-purple-500 focus:bg-white transition-all`}
                aria-invalid={!!passwordError}
                aria-describedby={passwordError ? "login-password-error" : undefined}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 touch-manipulation min-h-[44px] min-w-[44px] justify-center cursor-pointer"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {passwordError && (
              <p id="login-password-error" className="text-xs text-rose-600 font-medium">
                {passwordError}
              </p>
            )}
          </div>

          {/* Remember Me Checkbox */}
          <div className="flex items-center">
            <label className="flex items-center gap-2.5 cursor-pointer text-xs font-medium text-slate-600 touch-manipulation">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 rounded border-slate-300 text-purple-600 focus:ring-purple-500 touch-manipulation cursor-pointer"
              />
              <span>Remember me on this device</span>
            </label>
          </div>

          {/* Login Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3.5 px-4 text-sm font-bold text-white bg-gradient-to-r from-pink-500 via-purple-600 to-indigo-600 hover:opacity-95 disabled:opacity-60 rounded-xl shadow-md min-h-[44px] touch-manipulation flex items-center justify-center gap-2 transition-all cursor-pointer mt-1"
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
              <div className="w-full border-t border-slate-200" />
            </div>
            <span className="relative bg-white px-3 text-xs uppercase font-semibold text-slate-400">
              or
            </span>
          </div>

          {/* Optional Demo Social Logins */}
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => handleSocialClick("Google")}
              className="py-2.5 px-3 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 flex items-center justify-center gap-2 touch-manipulation min-h-[44px] cursor-pointer"
            >
              <span>Google (Demo)</span>
            </button>
            <button
              type="button"
              onClick={() => handleSocialClick("Apple")}
              className="py-2.5 px-3 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 flex items-center justify-center gap-2 touch-manipulation min-h-[44px] cursor-pointer"
            >
              <span>Apple (Demo)</span>
            </button>
          </div>

          {/* Create Account Section */}
          <div className="text-center pt-3 border-t border-slate-100">
            <p className="text-xs text-slate-500">
              New to CosmeticVerify?{" "}
              <button
                type="button"
                onClick={onSwitchToSignup}
                className="font-bold text-purple-700 hover:underline min-h-[44px] inline-flex items-center touch-manipulation cursor-pointer"
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
