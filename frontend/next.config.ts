import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        // Proxy API requests to the backend
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*'
      }
    ];
  }
};

export default nextConfig;
