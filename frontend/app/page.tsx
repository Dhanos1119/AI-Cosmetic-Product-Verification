"use client";

import { useState, useEffect, useRef } from "react";
import Header from "../components/Header";
import Hero from "../components/Hero";
import VerificationWorkspace from "../components/VerificationWorkspace";
import Features from "../components/Features";
import HowItWorks from "../components/HowItWorks";
import AboutSection from "../components/AboutSection";
import Footer from "../components/Footer";
import LoginModal from "../components/LoginModal";
import SignupModal from "../components/SignupModal";
import ForgotPasswordModal from "../components/ForgotPasswordModal";
import LogoutConfirmModal from "../components/LogoutConfirmModal";
import CameraModal from "../components/CameraModal";
import FeatureDetailModal, { FeatureItem } from "../components/FeatureDetailModal";
import { AiAnalysisResult } from "../components/VerificationResult";
import { toast } from "react-toastify";

type AuthModalState = "closed" | "login" | "signup" | "forgot";

export default function Home() {
  // Authentication State
  const [user, setUser] = useState<{ email: string; name: string } | null>(null);
  const [authModalState, setAuthModalState] = useState<AuthModalState>("closed");
  const [isLogoutConfirmOpen, setIsLogoutConfirmOpen] = useState(false);

  // Modals State
  const [isCameraModalOpen, setIsCameraModalOpen] = useState(false);
  const [selectedFeature, setSelectedFeature] = useState<FeatureItem | null>(null);

  // Upload & AI Analysis State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [productUrl, setProductUrl] = useState<string>("");
  const [aiAnalysisResult, setAiAnalysisResult] = useState<AiAnalysisResult | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasVerified, setHasVerified] = useState(false);

  // In-flight request cancellation reference
  const abortControllerRef = useRef<AbortController | null>(null);

  // Restore authenticated session from localStorage on mount
  useEffect(() => {
    try {
      const savedUser = localStorage.getItem("cosmetic_verify_user");
      if (savedUser) {
        setUser(JSON.parse(savedUser));
      }
    } catch (e) {
      console.warn("Session restore notice:", e);
    }
  }, []);

  // Clean up Object URL and any active requests on unmount
  useEffect(() => {
    return () => {
      if (previewUrl && previewUrl.startsWith("blob:")) {
        URL.revokeObjectURL(previewUrl);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, [previewUrl]);

  // Cancel any active verification request
  const handleCancelVerification = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort("User cancelled verification");
      abortControllerRef.current = null;
    }
    setIsAnalyzing(false);
    toast.info("Verification cancelled.", { toastId: "cancelled-toast" });
  };

  // Handlers for File Selection (Logged-in only)
  const handleFileSelect = (file: File) => {
    if (!user) {
      toast.info("Please sign in to upload and verify a cosmetic product.", {
        toastId: "auth-required-upload",
      });
      setAuthModalState("login");
      return;
    }

    // Cancel any previous in-flight request when a new image is chosen
    if (abortControllerRef.current) {
      abortControllerRef.current.abort("New image selected");
      abortControllerRef.current = null;
    }

    if (previewUrl && previewUrl.startsWith("blob:")) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    setAiAnalysisResult(null);
    setAnalysisError(null);
    setHasVerified(false);
    setIsAnalyzing(false);
  };

  const handleFileRemove = () => {
    // Cancel any ongoing analysis if the file is removed
    if (abortControllerRef.current) {
      abortControllerRef.current.abort("Image removed");
      abortControllerRef.current = null;
    }
    if (previewUrl && previewUrl.startsWith("blob:")) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setAiAnalysisResult(null);
    setAnalysisError(null);
    setHasVerified(false);
    setIsAnalyzing(false);
  };

  // Open Camera Trigger (Protected)
  const handleOpenCamera = () => {
    if (!user) {
      toast.info("Please sign in to use the camera verification feature.", {
        toastId: "auth-required-camera",
      });
      setAuthModalState("login");
      return;
    }
    setIsCameraModalOpen(true);
  };

  // Start Verification Trigger (Sends image to FastAPI AI Service via Backend Gateway)
  const handleStartVerification = async (e?: React.MouseEvent) => {
    if (e) {
      e.stopPropagation();
      e.preventDefault();
    }

    if (isAnalyzing) return; // Guard against duplicate submissions

    if (!user) {
      toast.info("Please sign in or create an account to start verification.", {
        toastId: "auth-required-verify",
      });
      setAuthModalState("login");
      return;
    }

    if (!selectedFile) {
      toast.error("Please upload or capture a cosmetic product image first.", {
        toastId: "no-image-verify",
      });
      const workspaceEl = document.getElementById("verification-workspace");
      if (workspaceEl) {
        workspaceEl.scrollIntoView({ behavior: "smooth" });
      }
      return;
    }

    // Cancel any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort("New request started");
    }

    const controller = new AbortController();
    abortControllerRef.current = controller;

    // 25-second client-side timeout safety
    const timeoutId = setTimeout(() => {
      if (abortControllerRef.current === controller) {
        controller.abort("Verification request timed out. Please try again.");
      }
    }, 25000);

    setIsAnalyzing(true);
    setAnalysisError(null);

    try {
      const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || `http://${host}:5000/api/upload`;

      const formData = new FormData();
      formData.append("file", selectedFile);
      if (productUrl.trim()) {
        formData.append("product_url", productUrl.trim());
      }

      const response = await fetch(backendUrl, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const data = await response.json();

      // Handle non-cosmetic rejection response
      if (data.status === "rejected_non_cosmetic" || data.message?.includes("Non-cosmetic")) {
        setAiAnalysisResult(null);
        setHasVerified(false);
        const nonCosmeticMsg = data.message || "Non-cosmetic image detected.";
        setAnalysisError(nonCosmeticMsg);
        toast.warn(nonCosmeticMsg, {
          toastId: "non-cosmetic-toast",
        });
        return;
      }

      if (!response.ok || !data.success) {
        throw new Error(data.message || data.detail || "Cosmetic verification service failed.");
      }

      setAiAnalysisResult(data);
      setHasVerified(true);
      toast.success("Verification complete! Check your results below.", {
        toastId: "verify-success",
      });

      setTimeout(() => {
        const resultEl = document.getElementById("verification-results-container");
        if (resultEl) {
          resultEl.scrollIntoView({ behavior: "smooth" });
        }
      }, 100);
    } catch (err: any) {
      clearTimeout(timeoutId);

      if (err.name === "AbortError" || controller.signal.aborted) {
        const reason = controller.signal.reason || "Verification was cancelled.";
        console.log("Verification aborted:", reason);
        if (typeof reason === "string" && reason.includes("timed out")) {
          setAnalysisError("The verification request timed out. Please check your image and try again.");
          toast.error("Verification timed out.", { toastId: "timeout-toast" });
        }
        return;
      }

      const errorMsg = err.message || "Unable to connect to verification service. Please try again.";
      setAnalysisError(errorMsg);
      console.error("CosmeticVerify Gateway Error:", err);
      toast.error(errorMsg, {
        toastId: "upload-error-toast",
      });
    } finally {
      clearTimeout(timeoutId);
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
      }
      setIsAnalyzing(false);
    }
  };


  const handleResetVerification = () => {
    setHasVerified(false);
    setAiAnalysisResult(null);
    setAnalysisError(null);
    setProductUrl("");
    handleFileRemove();
    const workspaceEl = document.getElementById("verification-workspace");
    if (workspaceEl) {
      workspaceEl.scrollIntoView({ behavior: "smooth" });
    }
  };

  const handleLoginSuccess = (loggedInUser: { email: string; name: string }) => {
    setUser(loggedInUser);
    setAuthModalState("closed");
    // Note: The single "Login successful!" toast is displayed by LoginModal to prevent duplicate notifications.
  };

  const handleConfirmLogout = () => {
    setUser(null);
    try {
      localStorage.removeItem("cosmetic_verify_user");
      localStorage.removeItem("cosmetic_verify_token");
    } catch (e) {
      console.warn("Storage clear notice:", e);
    }
    setIsLogoutConfirmOpen(false);
    handleFileRemove();
    toast.info("You have been signed out.", {
      toastId: "logout-info-toast",
    });
  };

  const handleScrollTo = (elementId: string) => {
    const el = document.getElementById(elementId);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0B0B12] text-[#F8FAFC] selection:bg-purple-900/60 selection:text-pink-300 overflow-x-hidden">
      {/* Header Navigation */}
      <Header
        user={user}
        onOpenLogin={() => setAuthModalState("login")}
        onOpenSignup={() => setAuthModalState("signup")}
        onLogout={() => setIsLogoutConfirmOpen(true)}
        onNavigateToWorkspace={() => handleScrollTo("verification-workspace")}
      />

      <main className="flex-1">
        {/* Hero Section */}
        <Hero
          user={user}
          onStartVerification={() => {
            if (!user) {
              toast.info("Please sign in or create an account to start verification.", {
                toastId: "hero-auth-prompt",
              });
              setAuthModalState("login");
            } else {
              handleScrollTo("verification-workspace");
            }
          }}
          onHowItWorks={() => {
            if (user) {
              handleScrollTo("verification-workspace");
            } else {
              handleScrollTo("how-it-works");
            }
          }}
        />

        {/* Verification Workspace (Logged-In vs Logged-Out states) */}
        <VerificationWorkspace
          user={user}
          selectedFile={selectedFile}
          previewUrl={previewUrl}
          productUrl={productUrl}
          onProductUrlChange={setProductUrl}
          aiAnalysisResult={aiAnalysisResult}
          analysisError={analysisError}
          isAnalyzing={isAnalyzing}
          hasVerified={hasVerified}
          onFileSelect={handleFileSelect}
          onFileRemove={handleFileRemove}
          onOpenCamera={handleOpenCamera}
          onStartVerification={handleStartVerification}
          onCancelVerification={handleCancelVerification}
          onResetVerification={handleResetVerification}
          onOpenLogin={() => setAuthModalState("login")}
          onOpenSignup={() => setAuthModalState("signup")}
        />

        {/* Feature Cards Section */}
        <Features onSelectFeature={(feature) => setSelectedFeature(feature)} />

        {/* How It Works Section */}
        <HowItWorks />

        {/* About Section */}
        <AboutSection />
      </main>

      {/* Footer */}
      <Footer />

      {/* Auth Modals */}
      <LoginModal
        isOpen={authModalState === "login"}
        onClose={() => setAuthModalState("closed")}
        onLoginSuccess={handleLoginSuccess}
        onSwitchToSignup={() => setAuthModalState("signup")}
        onSwitchToForgot={() => setAuthModalState("forgot")}
      />

      <SignupModal
        isOpen={authModalState === "signup"}
        onClose={() => setAuthModalState("closed")}
        onSwitchToLogin={() => setAuthModalState("login")}
      />

      <ForgotPasswordModal
        isOpen={authModalState === "forgot"}
        onClose={() => setAuthModalState("closed")}
        onBackToLogin={() => setAuthModalState("login")}
      />

      <LogoutConfirmModal
        isOpen={isLogoutConfirmOpen}
        onClose={() => setIsLogoutConfirmOpen(false)}
        onConfirmLogout={handleConfirmLogout}
      />

      {/* Camera Modal */}
      <CameraModal
        isOpen={isCameraModalOpen}
        onClose={() => setIsCameraModalOpen(false)}
        onPhotoCaptured={handleFileSelect}
      />

      {/* Feature Details Specification Modal */}
      <FeatureDetailModal
        feature={selectedFeature}
        onClose={() => setSelectedFeature(null)}
      />
    </div>
  );
}
