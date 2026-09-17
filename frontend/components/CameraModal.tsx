"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Camera, X, RefreshCw, Check, AlertTriangle, Video } from "lucide-react";
import { toast } from "react-toastify";

interface CameraModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPhotoCaptured: (file: File) => void;
}

export default function CameraModal({ isOpen, onClose, onPhotoCaptured }: CameraModalProps) {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [capturedBlob, setCapturedBlob] = useState<Blob | null>(null);
  const [capturedPreviewUrl, setCapturedPreviewUrl] = useState<string | null>(null);
  const [facingMode, setFacingMode] = useState<"environment" | "user">("environment");
  const [isInitializing, setIsInitializing] = useState(false);

  const videoRef = useRef<HTMLVideoElement>(null);

  // Helper to stop all stream tracks
  const stopStreamTracks = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  }, [stream]);

  // Clean up stream on unmount or close
  const handleClose = useCallback(() => {
    stopStreamTracks();
    if (capturedPreviewUrl) {
      URL.revokeObjectURL(capturedPreviewUrl);
      setCapturedPreviewUrl(null);
    }
    setCapturedBlob(null);
    setCameraError(null);
    onClose();
  }, [stopStreamTracks, capturedPreviewUrl, onClose]);

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

  // Start camera stream
  const startCamera = useCallback(async (mode: "environment" | "user") => {
    setCameraError(null);
    setIsInitializing(true);

    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("UNSUPPORTED_BROWSER");
      }

      const newStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: mode,
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });

      setStream(newStream);
      if (videoRef.current) {
        videoRef.current.srcObject = newStream;
      }
    } catch (err: unknown) {
      console.error("Camera access error:", err);
      const errorObj = err as { name?: string; message?: string };
      if (
        errorObj.name === "NotAllowedError" ||
        errorObj.name === "PermissionDeniedError" ||
        errorObj.message === "Permission denied"
      ) {
        const errMsg = "Camera permission was denied. Please allow camera access in your browser settings or upload an image instead.";
        setCameraError(errMsg);
        toast.error(errMsg, { toastId: "camera-perm-denied" });
      } else if (errorObj.message === "UNSUPPORTED_BROWSER") {
        const warnMsg = "Camera access is not supported by your browser or secure context (HTTPS/localhost required). Please upload an image file instead.";
        setCameraError(warnMsg);
        toast.warning(warnMsg, { toastId: "camera-unsupported" });
      } else {
        const errMsg = "Unable to access camera device. Please ensure a camera is connected and allowed, or upload an image file instead.";
        setCameraError(errMsg);
        toast.error(errMsg, { toastId: "camera-access-error" });
      }
    } finally {
      setIsInitializing(false);
    }
  }, [stream]);

  // Initial effect when modal opens
  useEffect(() => {
    if (isOpen && !capturedBlob) {
      startCamera(facingMode);
    }

    return () => {
      stopStreamTracks();
    };
  }, [isOpen]);

  // Attach stream to video element
  useEffect(() => {
    if (videoRef.current && stream && !capturedBlob) {
      videoRef.current.srcObject = stream;
    }
  }, [stream, capturedBlob]);

  // Keyboard escape handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        handleClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, handleClose]);

  if (!isOpen) return null;

  // Capture current video frame
  const capturePhoto = () => {
    if (!videoRef.current) return;

    const video = videoRef.current;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (blob) {
          setCapturedBlob(blob);
          const preview = URL.createObjectURL(blob);
          setCapturedPreviewUrl(preview);
          stopStreamTracks();
          toast.success("Camera frame captured successfully.", {
            toastId: "camera-capture-success",
          });
        }
      },
      "image/png",
      0.95
    );
  };

  const handleRetake = () => {
    if (capturedPreviewUrl) {
      URL.revokeObjectURL(capturedPreviewUrl);
      setCapturedPreviewUrl(null);
    }
    setCapturedBlob(null);
    startCamera(facingMode);
  };

  const handleConfirmUse = () => {
    if (capturedBlob) {
      const capturedFile = new File([capturedBlob], `cosmetic_scan_${Date.now()}.png`, {
        type: "image/png",
      });
      onPhotoCaptured(capturedFile);
      handleClose();
    }
  };

  const toggleCameraFacingMode = () => {
    const nextMode = facingMode === "environment" ? "user" : "environment";
    setFacingMode(nextMode);
    startCamera(nextMode);
  };

  return (
    <div
      className="fixed inset-0 z-[300] flex items-center justify-center p-3 sm:p-4 bg-slate-950/80 backdrop-blur-md overflow-y-auto animate-fadeIn pointer-events-auto modal-scroll-container"
      role="dialog"
      aria-modal="true"
      aria-labelledby="camera-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) handleClose();
      }}
    >
      <div
        className="relative w-full bg-slate-900 rounded-3xl shadow-2xl border border-purple-900/50 overflow-hidden flex flex-col text-white my-auto focus:outline-none z-[310] pointer-events-auto"
        style={{ width: "min(100% - 24px, 560px)", maxHeight: "calc(100dvh - 24px)" }}
      >
        {/* Header */}
        <div className="p-4 sm:p-5 bg-slate-950 border-b border-slate-800 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-pink-500/20 border border-pink-400/30 flex items-center justify-center text-pink-400">
              <Camera className="w-4 h-4" />
            </div>
            <div>
              <h2 id="camera-modal-title" className="text-base sm:text-lg font-bold text-white leading-tight">
                Cosmetic Product Camera Scanner
              </h2>
              <p className="text-[11px] text-purple-300">Live Device Frame Capture</p>
            </div>
          </div>

          <button
            type="button"
            onClick={handleClose}
            className="text-slate-400 hover:text-white p-2.5 rounded-full hover:bg-slate-800 transition-colors focus:outline-none focus:ring-2 focus:ring-pink-400 touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer z-10"
            aria-label="Close camera modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Viewport */}
        <div className="relative bg-black flex-1 min-h-[260px] sm:min-h-[360px] flex items-center justify-center overflow-hidden">
          {cameraError ? (
            <div className="p-6 text-center max-w-md space-y-4">
              <div className="w-14 h-14 rounded-full bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400 mx-auto">
                <AlertTriangle className="w-7 h-7" />
              </div>
              <p className="text-xs sm:text-sm font-medium text-slate-200 leading-relaxed">{cameraError}</p>
              <button
                type="button"
                onClick={() => startCamera(facingMode)}
                className="px-5 py-2.5 text-xs font-bold bg-purple-600 hover:bg-purple-500 text-white rounded-xl shadow-md transition-colors touch-manipulation min-h-[44px] cursor-pointer"
              >
                Try Again
              </button>
            </div>
          ) : capturedPreviewUrl ? (
            <div className="relative w-full h-full flex items-center justify-center">
              <img
                src={capturedPreviewUrl}
                alt="Captured cosmetic scan preview"
                className="max-h-[360px] w-auto object-contain rounded-lg"
              />
              <div className="absolute top-4 left-4 bg-emerald-500/90 text-white text-xs font-semibold px-3 py-1 rounded-full shadow-md backdrop-blur-xs flex items-center gap-1.5">
                <Check className="w-3.5 h-3.5" />
                <span>Frame Captured</span>
              </div>
            </div>
          ) : (
            <div className="relative w-full h-full flex items-center justify-center">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full max-h-[360px] object-cover"
              />

              <div className="absolute inset-6 border-2 border-pink-500/60 rounded-2xl pointer-events-none flex flex-col justify-between p-3">
                <div className="flex justify-between">
                  <div className="w-4 h-4 border-t-2 border-l-2 border-pink-400" />
                  <div className="w-4 h-4 border-t-2 border-r-2 border-pink-400" />
                </div>
                <div className="text-center text-[10px] sm:text-xs font-semibold text-pink-300 bg-slate-950/70 py-1 px-3 rounded-full mx-auto backdrop-blur-xs">
                  Center product label inside frame
                </div>
                <div className="flex justify-between">
                  <div className="w-4 h-4 border-b-2 border-l-2 border-pink-400" />
                  <div className="w-4 h-4 border-b-2 border-r-2 border-pink-400" />
                </div>
              </div>

              {isInitializing && (
                <div className="absolute inset-0 bg-slate-950/80 flex items-center justify-center gap-2 text-xs text-purple-300">
                  <RefreshCw className="w-4 h-4 animate-spin text-pink-400" />
                  <span>Accessing device camera...</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 sm:p-5 bg-slate-950 border-t border-slate-800 flex items-center justify-between gap-3 shrink-0">
          {!capturedPreviewUrl ? (
            <>
              <button
                type="button"
                onClick={toggleCameraFacingMode}
                disabled={!!cameraError || isInitializing}
                className="px-3.5 py-2.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-300 text-xs font-semibold rounded-xl flex items-center gap-2 transition-colors touch-manipulation min-h-[44px] cursor-pointer"
                title="Switch Camera (Front/Back)"
              >
                <Video className="w-4 h-4 text-purple-400" />
                <span className="hidden sm:inline">Flip Camera</span>
              </button>

              <button
                type="button"
                onClick={capturePhoto}
                disabled={!!cameraError || isInitializing || !stream}
                className="px-6 py-3 bg-gradient-to-r from-pink-500 via-purple-600 to-indigo-600 hover:opacity-95 disabled:opacity-50 text-white font-bold text-sm rounded-2xl shadow-lg flex items-center gap-2 transition-all touch-manipulation min-h-[44px] cursor-pointer"
              >
                <Camera className="w-4 h-4 text-pink-200" />
                <span>Capture Photo</span>
              </button>

              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-xl transition-colors touch-manipulation min-h-[44px] cursor-pointer"
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={handleRetake}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl flex items-center gap-2 transition-colors touch-manipulation min-h-[44px] cursor-pointer"
              >
                <RefreshCw className="w-4 h-4 text-purple-400" />
                <span>Retake</span>
              </button>

              <button
                type="button"
                onClick={handleConfirmUse}
                className="px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 hover:opacity-95 text-white font-bold text-sm rounded-2xl shadow-lg flex items-center gap-2 transition-all touch-manipulation min-h-[44px] cursor-pointer"
              >
                <Check className="w-4 h-4" />
                <span>Use Captured Photo</span>
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
