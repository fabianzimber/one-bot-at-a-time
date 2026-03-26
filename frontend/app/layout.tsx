import type { Metadata, Viewport } from "next";
import { IBM_Plex_Mono, Space_Grotesk } from "next/font/google";
import { BotIdClient } from "botid/client";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  display: "swap",
});

const ibmPlexMono = IBM_Plex_Mono({
  variable: "--font-ibm-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "one-bot-at-a-time",
    template: "%s | one-bot-at-a-time",
  },
  description:
    "Minimalistische Work-in-Progress-Oberflaeche fuer den Trenkwalder AI Assistant, aufgebaut mit Next.js 16.2.1, Tailwind CSS und shadcn/ui.",
  applicationName: "one-bot-at-a-time",
};

export const viewport: Viewport = {
  colorScheme: "dark",
  themeColor: "#0D1117",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="de"
      suppressHydrationWarning
      className={`${spaceGrotesk.variable} ${ibmPlexMono.variable} dark h-full scroll-smooth antialiased`}
    >
      <head>
        <BotIdClient
          protect={[
            {
              path: "/api/*",
              method: "POST",
            },
          ]}
        />
      </head>
      <body className="min-h-full bg-background text-foreground selection:bg-brand-electric-indigo/35 selection:text-brand-white">
        {children}
      </body>
    </html>
  );
}
