import type { Metadata } from "next";
import localFont from "next/font/local";

import { ThemeProvider } from "@/themes/theme-provider";

import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});

const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "ResumeAI",
  description: "AI-powered resume analysis and job matching",
};

/**
 * Runs synchronously before first paint: reads the saved theme from
 * localStorage and sets it on <html>, so the user never sees a flash of
 * the wrong theme. Fails silently where storage is blocked.
 */
const themeInitScript = `
(function () {
  try {
    var t = localStorage.getItem("resumeai-theme");
    if (t) document.documentElement.setAttribute("data-theme", t);
  } catch (e) {}
})();
`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="plum-sky" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
