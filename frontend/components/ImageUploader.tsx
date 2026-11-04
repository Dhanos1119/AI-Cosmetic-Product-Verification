"use client";

import { useRef, useState, DragEvent, ChangeEvent } from "react";
import { Camera, Upload, Image as ImageIcon, X, CheckCircle } from "lucide-react";
import { toast } from "react-toastify";

interface ImageUploaderProps {
  selectedFile: File | null;
  previewUrl: string | null;
  onFileSelect: (file: File) => void;
  onFileRemove: () => void;
  onOpenCamera: () => void;
}

/**
 * Client-side downscaling of oversized images using an HTML5 offscreen canvas.
 * Reduces 10MB+ high-resolution camera photos to <= 1600px width/height while preserving aspect ratio.
 */
async function safelyResizeImage(file: File, maxDim: number = 1600): Promise<File> {
  return new Promise((resolve) => {
    // If SVG or already small, return original
    if (file.size < 1.5 * 1024 * 1024 && file.type === "image/jpeg") {
      return resolve(file);
    }

    const img = new Image();
    const objectUrl = URL.createObjectURL(file);

    img.onload = () => {
      URL.revokeObjectURL(objectUrl);
      const { naturalWidth: width, naturalHeight: height } = img;

      // If dimensions are within maxDim, preserve file
      if (width <= maxDim && height <= maxDim) {
        return resolve(file);
      }

      const scale = maxDim / Math.max(width, height);
      const newWidth = Math.max(1, Math.round(width * scale));
      const newHeight = Math.max(1, Math.round(height * scale));

      const canvas = document.createElement("canvas");
      canvas.width = newWidth;
      canvas.height = newHeight;
      const ctx = canvas.getContext("2d");

      if (!ctx) {
        return resolve(file);
      }

      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = "high";
      ctx.drawImage(img, 0, 0, newWidth, newHeight);

      canvas.toBlob(
        (blob) => {
          if (!blob) return resolve(file);
          const resizedFile = new File([blob], file.name.replace(/\.[^/.]+$/, "") + ".jpg", {
            type: "image/jpeg",
            lastModified: Date.now(),
          });
          resolve(resizedFile);
        },
        "image/jpeg",
        0.92
      );
    };

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      resolve(file);
    };

    img.src = objectUrl;
  });
}

export default function ImageUploader({
  selectedFile,
  previewUrl,
  onFileSelect,
  onFileRemove,
  onOpenCamera,
}: ImageUploaderProps) {
  const [dragActive, setDragActive] = useState(false);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const MAX_SIZE_BYTES = 15 * 1024 * 1024; // 15 MB limit

  const handleValidateAndSelect = async (file: File) => {
    // Validate type
    const validTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
    const fileType = file.type.toLowerCase();
    const fileName = file.name.toLowerCase();
    const isValidFormat =
      validTypes.includes(fileType) ||
      fileName.endsWith(".jpg") ||
      fileName.endsWith(".jpeg") ||
      fileName.endsWith(".png") ||
      fileName.endsWith(".webp");

    if (!isValidFormat) {
      toast.error("Only image files (JPG, JPEG, PNG, WEBP) are allowed.", {
        toastId: "invalid-format-toast",
      });
      return;
    }

    // Validate size (15MB limit)
    if (file.size > MAX_SIZE_BYTES) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
      toast.error(`File size exceeds 15 MB limit (${sizeMB} MB uploaded).`, {
        toastId: "file-size-toast",
      });
      return;
    }

    // Safely downscale oversized photo in background for high-speed AI inference
    try {
      setIsOptimizing(true);
      const optimizedFile = await safelyResizeImage(file, 1600);
      setIsOptimizing(false);
      onFileSelect(optimizedFile);
      toast.success("Product image ready for verification.", {
        toastId: "image-loaded-toast",
      });
    } catch {
      setIsOptimizing(false);
      onFileSelect(file);
    }
  };

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleValidateAndSelect(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleValidateAndSelect(e.target.files[0]);
    }
  };

  const handleRemove = () => {
    onFileRemove();
    toast.info("Product image removed.", {
      toastId: "image-removed-toast",
    });
  };

  return (
    <div className="w-full space-y-4">
      {/* Hidden input element */}
      <input
        ref={fileInputRef}
        type="file"
        id="cosmetic-file-upload-input"
        accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={handleChange}
      />

      {/* Upload Zone or Selected Preview */}
      {!selectedFile ? (
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative border-2 border-dashed rounded-3xl p-8 sm:p-12 text-center cursor-pointer transition-all duration-200 touch-manipulation ${
            dragActive
              ? "border-[#EC4899] bg-[#202033] scale-[1.01]"
              : "border-[#303047] hover:border-[#A855F7] bg-[#191925]/90 hover:bg-[#202033]/90"
          }`}
          tabIndex={0}
          role="button"
          aria-label="Upload or drag cosmetic product image area"
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              fileInputRef.current?.click();
            }
          }}
        >
          <div className="flex flex-col items-center justify-center space-y-5">
            {/* Upload Icon Circle */}
            <div className="w-20 h-20 rounded-3xl bg-[#12121C] border border-[#303047] flex items-center justify-center shadow-md">
              <Upload className="w-9 h-9 text-[#EC4899]" />
            </div>

            {/* Title & Instructions */}
            <div className="space-y-1">
              <h3 className="text-xl sm:text-2xl font-bold text-[#F8FAFC]">
                Upload cosmetic packaging photo
              </h3>
              <p className="text-sm text-[#A1A1B5] font-medium max-w-sm mx-auto">
                Drag and drop your file here, click to browse, or use your device camera
              </p>
            </div>

            {/* Camera & Browse Action Buttons */}
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onOpenCamera();
                }}
                className="inline-flex items-center gap-2 px-5 py-3 text-xs font-bold text-[#F8FAFC] bg-[#12121C] hover:bg-[#202033] border border-[#303047] rounded-xl transition-colors shadow-sm touch-manipulation min-h-[44px] cursor-pointer"
              >
                <Camera className="w-4 h-4 text-[#A855F7]" />
                <span>Use Device Camera</span>
              </button>

              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
                className="inline-flex items-center gap-2 px-5 py-3 text-xs font-bold text-white bg-gradient-to-r from-[#EC4899] to-[#A855F7] hover:opacity-95 rounded-xl transition-all shadow-md touch-manipulation min-h-[44px] cursor-pointer"
              >
                <Upload className="w-4 h-4" />
                <span>Browse File</span>
              </button>
            </div>

            {/* Supported formats */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#12121C] border border-[#303047] text-xs font-medium text-[#A1A1B5]">
              <ImageIcon className="w-3.5 h-3.5 text-[#A855F7]" />
              <span>JPG, JPEG, PNG, WEBP (Max file size: 15 MB)</span>
            </div>
          </div>
        </div>
      ) : (
        /* Selected File Card */
        <div className="p-6 bg-[#191925] rounded-3xl border border-[#303047] flex flex-col sm:flex-row items-center justify-between gap-6 shadow-xl">
          <div className="flex items-center gap-5 w-full sm:w-auto">
            {previewUrl && (
              <div className="w-24 h-24 rounded-2xl overflow-hidden bg-[#12121C] border border-[#303047] shrink-0 shadow-md relative">
                <img
                  src={previewUrl}
                  alt="Selected product preview"
                  className="w-full h-full object-cover"
                />
              </div>
            )}
            <div className="space-y-1.5 overflow-hidden">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-[#22C55E] shrink-0" />
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#22C55E] bg-[#22C55E]/10 px-2 py-0.5 rounded-md border border-[#22C55E]/30">
                  {isOptimizing ? "Optimizing..." : "Image Ready"}
                </span>
              </div>
              <p className="font-bold text-[#F8FAFC] truncate max-w-xs sm:max-w-md text-base">
                {selectedFile.name}
              </p>
              <p className="text-xs text-[#A1A1B5] font-medium">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • {selectedFile.type.split("/")[1]?.toUpperCase() || "IMAGE"}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto justify-end">
            <button
              type="button"
              onClick={onOpenCamera}
              className="inline-flex items-center gap-1.5 px-3.5 py-2.5 text-xs font-semibold text-[#A855F7] bg-[#202033] hover:bg-[#12121C] border border-[#303047] rounded-xl transition-colors touch-manipulation min-h-[44px] cursor-pointer"
            >
              <Camera className="w-3.5 h-3.5" />
              <span>Camera</span>
            </button>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 text-xs font-semibold text-[#F8FAFC] bg-[#202033] hover:bg-[#12121C] border border-[#303047] rounded-xl transition-colors touch-manipulation min-h-[44px] cursor-pointer"
            >
              <span>Change Image</span>
            </button>

            <button
              type="button"
              onClick={handleRemove}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 text-xs font-semibold text-[#F87171] bg-[#12121C] hover:bg-[#202033] border border-[#303047] rounded-xl transition-colors touch-manipulation min-h-[44px] cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
              <span>Remove</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
