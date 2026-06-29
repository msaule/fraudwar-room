const isGitHubPages = process.env.GITHUB_PAGES === 'true'

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: isGitHubPages ? 'export' : undefined,
  basePath: isGitHubPages ? '/fraudwar-room' : undefined,
  assetPrefix: isGitHubPages ? '/fraudwar-room/' : undefined,
  trailingSlash: isGitHubPages,
  images: {
    unoptimized: true
  }
}

module.exports = nextConfig
