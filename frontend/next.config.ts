import type { NextConfig } from "next";

const API =
  process.env.JYOTISH_API_URL ||
  (process.env.NODE_ENV === "production"
    ? "https://fashionatdoor-api-production.up.railway.app"
    : "http://localhost:8000");

const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API}/api/:path*` }];
  },
};

export default nextConfig;
