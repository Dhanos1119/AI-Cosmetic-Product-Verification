"use client";

import { useEffect } from "react";
import { LogOut, X } from "lucide-react";

interface LogoutConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirmLogout: () => void;
}

export default function LogoutConfirmModal({ isOpen, onClose, onConfirmLogout }: LogoutConfirmModalProps) {
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

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-3 sm:p-4 bg-[#0B0B12]/80 backdrop-blur-md animate-fadeIn pointer-events-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="logout-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="relative w-full bg-[#191925] rounded-3xl shadow-2xl border border-[#303047] overflow-hidden text-[#F8FAFC] focus:outline-none p-6 sm:p-7 space-y-5 my-auto z-[210] pointer-events-auto"
        style={{ width: "min(100% - 24px, 420px)" }}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 text-[#A1A1B5] hover:text-[#F8FAFC] p-2 rounded-full hover:bg-[#202033] transition-colors touch-manipulation min-h-[44px] min-w-[44px] flex items-center justify-center cursor-pointer z-10"
          aria-label="Close modal"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-[#F87171]/15 text-[#F87171] border border-[#F87171]/30 flex items-center justify-center shrink-0">
            <LogOut className="w-6 h-6" />
          </div>
          <div>
            <h3 id="logout-modal-title" className="text-lg font-bold text-[#F8FAFC]">
              Sign Out Confirmation
            </h3>
            <p className="text-xs text-[#A1A1B5]">
              Are you sure you want to sign out of your account?
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-3 px-4 text-xs font-semibold text-[#F8FAFC] bg-[#12121C] hover:bg-[#202033] border border-[#303047] rounded-xl transition-colors min-h-[44px] touch-manipulation cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirmLogout}
            className="flex-1 py-3 px-4 text-xs font-bold text-white bg-[#F87171] hover:bg-rose-600 rounded-xl transition-colors shadow-xs min-h-[44px] touch-manipulation cursor-pointer"
          >
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
