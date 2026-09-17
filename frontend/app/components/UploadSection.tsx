"use client";

import { useState, useRef, DragEvent, ChangeEvent } from "react";
import { Camera, Upload, Image as ImageIcon, X, CheckCircle, Info, Sparkles } from "lucide-react";

export default function UploadSection() {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    setErrorMessage(null);
    const validTypes = ["image/jpeg", "image/jpg", "image/png"];
    if (!validTypes.includes(file.type)) {
      setErrorMessage("Unsupported file format. Please upload a JPG, JPEG, or PNG image.");
      return;
    }

    setSelectedFile(file);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
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
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleReset = () => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setSelectedFile(null);
    setPreviewUrl(null);
    setErrorMessage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <section id="upload-section" className="py-16 md:py-24 bg-gradient-to-b from-transparent via-purple-50/40 to-transparent">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center space-y-3 mb-10">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-100/80 border border-purple-200 text-purple-900 text-xs font-semibold uppercase tracking-wider">
            <Camera className="w-3.5 h-3.5 text-purple-700" />
            <span>Product Image Analysis</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
            Upload & Verify Cosmetic Product
          </h2>
          <p className="text-slate-600 max-w-xl mx-auto text-base">
            Select or drag a photo of your cosmetic product package, container, or ingredient label to get started.
          </p>
        </div>

        {/* Upload Container Card */}
        <div className="glass-card rounded-3xl p-6 sm:p-10 shadow-xl shadow-purple-900/5 border border-purple-150">
          <input
            ref={fileInputRef}
            type="file"
            id="cosmetic-image-input"
            accept=".jpg,.jpeg,.png"
            className="hidden"
            onChange={handleChange}
          />

          {!selectedFile ? (
            /* Drag & Drop Zone */
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`relative border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all duration-200 ${
                dragActive
                  ? "border-pink-500 bg-pink-50/60 scale-[1.01]"
                  : "border-purple-200 hover:border-purple-400 bg-white/60 hover:bg-purple-50/30"
              }`}
              tabIndex={0}
              role="button"
              aria-label="Upload cosmetic product image area"
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  fileInputRef.current?.click();
                }
              }}
            >
              <div className="flex flex-col items-center justify-center space-y-4">
                {/* Upload Icons Badge */}
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-pink-100 via-purple-100 to-indigo-100 flex items-center justify-center text-purple-700 shadow-inner group-hover:scale-110 transition-transform">
                  <div className="relative">
                    <Camera className="w-9 h-9 text-pink-600" />
                    <Upload className="w-5 h-5 text-purple-700 absolute -bottom-1 -right-1 bg-white rounded-full p-0.5 shadow-xs" />
                  </div>
                </div>

                {/* Main Instruction Text */}
                <div className="space-y-1">
                  <p className="text-xl font-bold text-slate-900">
                    Upload a cosmetic product image
                  </p>
                  <p className="text-sm text-slate-500 font-medium">
                    Drag and drop your image file here, or click to browse
                  </p>
                </div>

                {/* Formats Pill */}
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-600">
                  <ImageIcon className="w-3.5 h-3.5 text-purple-600" />
                  <span>Supported formats: JPG, JPEG, PNG</span>
                </div>
              </div>
            </div>
          ) : (
            /* Selected File State */
            <div className="space-y-6">
              <div className="p-6 bg-purple-50/50 rounded-2xl border border-purple-200/80 flex flex-col sm:flex-row items-center justify-between gap-6">
                <div className="flex items-center gap-5 w-full sm:w-auto">
                  {previewUrl && (
                    <div className="w-20 h-20 rounded-xl overflow-hidden bg-white border border-purple-200 shrink-0 shadow-xs relative">
                      <img
                        src={previewUrl}
                        alt="Selected cosmetic product preview"
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                  <div className="space-y-1 overflow-hidden">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span className="text-xs font-semibold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                        Image Loaded
                      </span>
                    </div>
                    <p className="font-bold text-slate-900 truncate max-w-xs sm:max-w-md">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • {selectedFile.type.split("/")[1]?.toUpperCase()}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
                  <button
                    type="button"
                    onClick={handleReset}
                    className="inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-semibold text-slate-700 bg-white hover:bg-slate-100 border border-slate-300 rounded-xl transition-colors"
                  >
                    <X className="w-4 h-4" />
                    <span>Remove</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="inline-flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-semibold text-purple-900 bg-purple-100 hover:bg-purple-200 rounded-xl transition-colors"
                  >
                    <span>Change Image</span>
                  </button>
                </div>
              </div>

              {/* Status Note */}
              <div className="p-4 bg-amber-50 border border-amber-200/80 rounded-xl text-amber-900 text-xs sm:text-sm flex items-start gap-3">
                <Info className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Demo Mode Active:</span> The upload interface is fully functional for image selection. Backend AI analysis pipelines will be integrated in upcoming releases.
                </div>
              </div>
            </div>
          )}

          {/* Error Message if wrong format */}
          {errorMessage && (
            <div className="mt-4 p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-900 text-xs sm:text-sm flex items-center justify-between">
              <span>{errorMessage}</span>
              <button
                type="button"
                onClick={() => setErrorMessage(null)}
                className="text-rose-600 font-bold hover:underline"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Bottom Guidance Info */}
          <div className="mt-6 pt-6 border-t border-purple-100/80 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-pink-500" />
              <span>Tip: Clear lighting on brand logos and text yields highest accuracy.</span>
            </div>
            <span className="font-semibold text-purple-700 bg-purple-50 px-2.5 py-1 rounded-full border border-purple-100">
              CosmeticVerify AI Ready
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
