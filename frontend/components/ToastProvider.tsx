"use client";

/**
 * ToastProvider — SSR-safe Toastify container.
 *
 * FIX: The previous version used useState(false) + useEffect to detect mobile
 * width, which caused a hydration mismatch:
 *   - Server renders: position="top-right"  (isMobile = false by default)
 *   - Mobile client: position="top-center"  (isMobile switches to true after mount)
 *
 * This mismatch is what triggered the "Issues: 1" Next.js dev overlay error.
 *
 * Solution: Remove the server/client branch entirely. Use a single responsive
 * position value, OR render the ToastContainer only after mount using a
 * client-side mount guard so it never participates in SSR at all.
 * The latter is cleanest — ToastContainer has no meaningful SSR output anyway.
 */

import { useEffect, useState } from "react";
import { ToastContainer } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

export default function ToastProvider() {
  // Mount guard: render nothing on the server. The ToastContainer
  // is purely client-side (it manages a portal into document.body).
  // Rendering it only after mount eliminates the SSR/client position
  // mismatch that was causing the "Issues: 1" hydration error.
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  // Determine position after mount — window is guaranteed to be available.
  const isMobile = window.innerWidth < 640;

  return (
    <ToastContainer
      position={isMobile ? "top-center" : "top-right"}
      autoClose={3200}
      hideProgressBar={false}
      newestOnTop={true}
      closeOnClick
      rtl={false}
      pauseOnFocusLoss
      draggable
      pauseOnHover
      limit={3}
      theme="light"
    />
  );
}
