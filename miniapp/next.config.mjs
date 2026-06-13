/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  // Serve local /public images directly (no runtime image optimizer needed in
  // the standalone container).
  images: { unoptimized: true },
};

export default nextConfig;
