/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
};

require('dotenv').config()

module.exports = {
  env: {
    BACKEND_URL: process.env.BACKEND_URL,
  },
}


export default nextConfig;
