import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /**
   * Security headers — tuned to allow PayPal SDK iframes & popups to work.
   *
   * KEY ISSUES FIXED:
   * 1. Cross-Origin-Opener-Policy (COOP): PayPal's popup needs to communicate back
   *    to the opener window. "same-origin" blocks this. We use "same-origin-allow-popups".
   * 2. Content-Security-Policy (CSP): PayPal SDK loads scripts from paypal.com/sandbox.paypal.com,
   *    renders iframes from paypal.com, and opens popups. All these must be whitelisted.
   */
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          // ── PayPal popup fix: allow popup windows to communicate back ──
          {
            key: "Cross-Origin-Opener-Policy",
            value: "same-origin-allow-popups",
          },
          // ── Embedder policy: needed for SharedArrayBuffer if used, but keep unsafe-none for PayPal ──
          {
            key: "Cross-Origin-Embedder-Policy",
            value: "unsafe-none",
          },
          // ── Allow PayPal, Google/GTM, and Facebook/Meta iframes & scripts ──
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              // PayPal, GTM, GA4, Google & Facebook scripts
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.paypal.com https://www.sandbox.paypal.com https://www.paypalobjects.com https://accounts.google.com https://www.googletagmanager.com https://tagmanager.google.com https://www.google-analytics.com https://ssl.google-analytics.com https://connect.facebook.net",
              // PayPal, GTM, GA4 & Google iframes
              "frame-src 'self' https://www.paypal.com https://www.sandbox.paypal.com https://*.paypal.com https://accounts.google.com https://www.googletagmanager.com https://tagmanager.google.com",
              // API calls to PayPal, Google, GTM, GA4, Facebook, backend, and CDNs
              "connect-src 'self' https://www.paypal.com https://www.sandbox.paypal.com https://api-m.paypal.com https://api-m.sandbox.paypal.com https://www.paypalobjects.com https://accounts.google.com https://oauth2.googleapis.com https://www.googleapis.com https://www.google-analytics.com https://*.google-analytics.com https://*.analytics.google.com https://*.g.doubleclick.net https://www.googletagmanager.com https://connect.facebook.net https://www.facebook.com ws: wss:",
              // Images from PayPal, Google, GTM, GA4, and Facebook (Pixel)
              "img-src 'self' data: blob: https://www.paypal.com https://www.paypalobjects.com https://www.sandbox.paypal.com https://lh3.googleusercontent.com https://www.googletagmanager.com https://www.google-analytics.com https://ssl.google-analytics.com https://*.google-analytics.com https://www.facebook.com",
              // Styles
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://www.paypalobjects.com https://tagmanager.google.com",
              // Fonts
              "font-src 'self' https://fonts.gstatic.com https://www.paypalobjects.com",
            ].join("; "),
          },
          // ── Standard security headers ──
          {
            key: "X-Frame-Options",
            value: "SAMEORIGIN",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
