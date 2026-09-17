"use client";

import { useState, useEffect } from "react";
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
  const [aiAnalysisResult, setAiAnalysisResult] = useState<AiAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [hasVerified, setHasVerified] = useState(false);

  // Clean up Object URL on unmount or file change
  useEffect(() => {
    return () => {
      if (previewUrl && previewUrl.startsWith("blob:")) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  // Handlers for File Selection (Logged-in only)
  const handleFileSelect = (file: File) => {
    if (!user) {
      toast.info("Please sign in to upload and verify a cosmetic product.", {
        toastId: "auth-required-upload",
      });
      setAuthModalState("login");
      return;
    }

    if (previewUrl && previewUrl.startsWith("blob:")) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    setAiAnalysisResult(null);
    setHasVerified(false);
  };

  const handleFileRemove = () => {
    if (previewUrl && previewUrl.startsWith("blob:")) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setAiAnalysisResult(null);
    setHasVerified(false);
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

  // Start Verification Trigger (Sends image to FastAPI AI Service on Port 8001)
  const handleStartVerification = async (e?: React.MouseEvent) => {
    if (e) {
      e.stopPropagation();
      e.preventDefault();
    }

    if (isAnalyzing) return; // Guard against double triggers

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

    // Diagnostic logs before sending request
    console.log("Selected file:", selectedFile);
    console.log("File name:", selectedFile.name);
    console.log("File type:", selectedFile.type);
    console.log("File size:", selectedFile.size);

    setIsAnalyzing(true);
    toast.info("Sending image to FastAPI AI Service (port 8001)...", {
      toastId: "analyzing-toast",
    });

    try {
      // Dynamic AI Service Host: resolves to 192.168.1.27 on mobile devices and localhost on PC
      const host = typeof window !== "undefined" ? window.location.hostname : "192.168.1.27";
      const aiServiceUrl = `http://${host}:8001/api/analyze`;

      // Build FormData using field name "file"
      const formData = new FormData();
      formData.append("file", selectedFile);

      // Fetch request without manual Content-Type header
      const response = await fetch(aiServiceUrl, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.message || data.detail || "FastAPI AI service analysis failed.");
      }

      console.log("FastAPI AI Analysis Response:", data);
      setAiAnalysisResult(data);
      setIsAnalyzing(false);
      setHasVerified(true);
      toast.success("AI analysis completed successfully!", {
        toastId: "verify-success",
      });

      setTimeout(() => {
        const resultEl = document.getElementById("verification-results-container");
        if (resultEl) {
          resultEl.scrollIntoView({ behavior: "smooth" });
        }
      }, 100);
    } catch (err: any) {
      setIsAnalyzing(false);
      console.error("FastAPI AI Service Error:", err);
      toast.error(err.message || "Unable to connect to AI Service at port 8001.", {
        toastId: "upload-error-toast",
      });
    }
  };

  const handleResetVerification = () => {
    setHasVerified(false);
    setAiAnalysisResult(null);
    handleFileRemove();
    const workspaceEl = document.getElementById("verification-workspace");
    if (workspaceEl) {
      workspaceEl.scrollIntoView({ behavior: "smooth" });
    }
  };

  const handleLoginSuccess = (loggedInUser: { email: string; name: string }) => {
    setUser(loggedInUser);
    setAuthModalState("closed");
    toast.success("Welcome back! You are signed in.", {
      toastId: "login-welcome-toast",
    });
  };

  const handleConfirmLogout = () => {
    setUser(null);
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
    <div className="min-h-screen flex flex-col bg-[#fdf8fa] selection:bg-pink-200 selection:text-pink-900 overflow-x-hidden">
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
          aiAnalysisResult={aiAnalysisResult}
          isAnalyzing={isAnalyzing}
          hasVerified={hasVerified}
          onFileSelect={handleFileSelect}
          onFileRemove={handleFileRemove}
          onOpenCamera={handleOpenCamera}
          onStartVerification={handleStartVerification}
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
