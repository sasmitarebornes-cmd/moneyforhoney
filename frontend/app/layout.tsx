import React from "react";
import "./globals.css";

export const metadata = {
  title: "MONEY For HONEY — Autonomous Trading System",
  description: "autonomous Trading system and build self wealth engine for the future",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 font-sans antialiased min-h-screen selection:bg-amber-500/30 selection:text-amber-200">
        {children}
      </body>
    </html>
  );
}
