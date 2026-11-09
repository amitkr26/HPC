import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BDW AI Console — Deep-Tech Hardware & Research Intelligence",
  description:
    "India's deep-tech reasoning console for Semiconductors, VLSI, HPC, and Research Labs. Powered by Qwen2.5-72B on a zero-cost A100 cluster.",
  applicationName: "BerojgarDegreeWala AI",
  keywords: [
    "VLSI",
    "semiconductor",
    "static timing analysis",
    "HPC",
    "DeepSpeed",
    "research intelligence",
  ],
};

export const viewport: Viewport = {
  themeColor: "#0f172a",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-dvh bg-slate-50 text-slate-950 antialiased">{children}</body>
    </html>
  );
}
