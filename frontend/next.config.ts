import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 1. Allow ngrok to talk to Next.js without warnings
  experimental: {
    serverActions: {
      allowedOrigins: ["*.ngrok-free.dev"],
    },
  },

  // 2. The Rewrite Rule
  async rewrites() {
    return [
      {
        // When the browser requests /api/...
        source: '/api/:path*',
        // Send it to Python, BUT keep the /api prefix!
        destination: 'http://127.0.0.1:8000/api/:path*', 
      },
    ];
  },
};

export default nextConfig;
