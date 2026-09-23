import type { NextConfig } from "next";

const apiBase = process.env.EXTERNAL_API_BASE_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
	reactStrictMode: true,
	experimental: {
		proxyClientMaxBodySize: "1000gb",
		proxyTimeout: 30 * 60 * 1000,
	},
	transpilePackages: [
		"@mantine/charts",
		"recharts",
		"@instance/ocean-module",
	],
	rewrites: async () => [
		{ source: "/api/external/:path*", destination: `${apiBase}/:path*` },
	],
};

export default nextConfig;
