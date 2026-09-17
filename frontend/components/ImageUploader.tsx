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

export default function ImageUploader({
  selectedFile,
  previewUrl,
  onFileSelect,
  onFileRemove,
  onOpenCamera,
}: ImageUploaderProps) {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB limit

  const handleValidateAndSelect = (file: File) => {
    // Validate type
    const validTypes = ["image/jpeg", "image/jpg", "image/png"];
    if (!validTypes.includes(file.type.toLowerCase())) {
      toast.error("Only image files (JPG, JPEG, PNG) are allowed.", {
        toastId: "invalid-format-toast",
      });
      return;
    }

    // Validate size (10MB limit)
    if (file.size > MAX_SIZE_BYTES) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
      toast.error(`File size exceeds 10 MB limit (${sizeMB} MB uploaded).`, {
        toastId: "file-size-toast",
      });
      return;
    }

    onFileSelect(file);
    toast.success("Product image loaded successfully.", {
      toastId: "image-loaded-toast",
    });
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
        accept=".jpg,.jpeg,.png,image/jpeg,image/png"
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
              ? "border-pink-500 bg-pink-50/70 scale-[1.01]"
              : "border-purple-200 hover:border-purple-400 bg-white/70 hover:bg-purple-50/40"
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
            <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-pink-100 via-purple-100 to-indigo-100 flex items-center justify-center text-purple-700 shadow-xs">
              <Upload className="w-9 h-9 text-pink-600" />
            </div>

            {/* Title & Instructions */}
            <div className="space-y-1">
              <h3 className="text-xl sm:text-2xl font-bold text-slate-900">
                Upload a cosmetic product image
              </h3>
              <p className="text-sm text-slate-500 font-medium max-w-sm mx-auto">
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
                className="inline-flex items-center gap-2 px-5 py-3 text-xs font-bold text-purple-900 bg-purple-100/90 hover:bg-purple-200 border border-purple-200/80 rounded-xl transition-colors shadow-2xs touch-manipulation min-h-[44px] cursor-pointer"
              >
                <Camera className="w-4 h-4 text-purple-700" />
                <span>Use Device Camera</span>
              </button>

              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
                className="inline-flex items-center gap-2 px-5 py-3 text-xs font-bold text-white bg-purple-900 hover:bg-purple-950 rounded-xl transition-colors shadow-2xs touch-manipulation min-h-[44px] cursor-pointer"
              >
                <Upload className="w-4 h-4" />
                <span>Browse File</span>
              </button>
            </div>

            {/* Supported formats */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-xs font-medium text-slate-600">
              <ImageIcon className="w-3.5 h-3.5 text-purple-600" />
              <span>JPG, JPEG, PNG (Max file size: 10 MB)</span>
            </div>
          </div>
        </div>
      ) : (
        /* Selected File Card */
        <div className="p-6 bg-purple-50/60 rounded-3xl border border-purple-200 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-xs">
          <div className="flex items-center gap-5 w-full sm:w-auto">
            {previewUrl && (
              <div className="w-24 h-24 rounded-2xl overflow-hidden bg-white border border-purple-200 shrink-0 shadow-xs relative">
                <img
                  src={previewUrl}
                  alt="Selected product preview"
                  className="w-full h-full object-cover"
                />
              </div>
            )}
            <div className="space-y-1.5 overflow-hidden">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
                <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                  Image Ready
                </span>
              </div>
              <p className="font-bold text-slate-900 truncate max-w-xs sm:max-w-md text-base">
                {selectedFile.name}
              </p>
              <p className="text-xs text-slate-500 font-medium">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • {selectedFile.type.split("/")[1]?.toUpperCase() || "IMAGE"}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto justify-end">
            <button
              type="button"
              onClick={onOpenCamera}
              className="inline-flex items-center gap-1.5 px-3.5 py-2.5 text-xs font-semibold text-purple-900 bg-purple-100 hover:bg-purple-200 border border-purple-200 rounded-xl transition-colors touch-manipulation min-h-[44px] cursor-pointer"
            >
              <Camera className="w-3.5 h-3.5" />
              <span>Camera</span>
            </button>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 text-xs font-semibold text-slate-800 bg-white hover:bg-slate-100 border border-slate-300 rounded-xl transition-colors touch-manipulation min-h-[44px] cursor-pointer"
            >
              <span>Change Image</span>
            </button>

            <button
              type="button"
              onClick={handleRemove}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded-xl transition-colors touch-manipulation min-h-[44px] cursor-pointer"
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
