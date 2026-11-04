import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /**
   * allowedDevOrigins: Permit the local network IP so real mobile devices
   * can load the dev server (Next.js 16 blocks cross-origin /_next/* requests
   * by default). Only the hostname is matched — no port, no scheme, no path.
   *
   * Add your machine's LAN IP here. If your IP changes, update this list.
   * This setting has no effect in production builds.
   */
  allowedDevOrigins: [
    "192.168.1.27",  // LAN IP for real-device testing
  ],

  /**
   * devIndicators: Move the dev overlay indicator to bottom-right.
   * Default is bottom-left which can overlap mobile navigation UI.
   * NOTE: This does NOT hide real errors — those still surface correctly.
   * Once all hydration errors are fixed, the "Issues" panel disappears on its own.
   */
  devIndicators: {
    position: "bottom-right",
  },
  experimental: {
    cpus: 1,
    workerThreads: false,
  },
};

export default nextConfig;
