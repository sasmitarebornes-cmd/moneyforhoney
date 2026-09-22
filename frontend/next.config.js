/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export", // Diubah dari "standalone" ke "export" agar bisa di-host di Cloudflare Pages
  images: {
    unoptimized: true, // Wajib untuk static export agar gambar (next/image) bisa dimuat tanpa server Node.js
  },
  reactStrictMode: true,
};

module.exports = nextConfig;