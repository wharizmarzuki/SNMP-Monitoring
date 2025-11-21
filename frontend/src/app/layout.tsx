import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "./Navbar";
import QueryProvider from "@/providers/QueryProvider";
import { UserProvider } from "@/providers/UserProvider";
import AuthGuard from "@/components/AuthGuard";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "SNMP Monitoring System",
  description: "Network monitoring dashboard with SNMP",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} font-sans antialiased`}>
        <QueryProvider>
          <UserProvider>
            <AuthGuard>
              <div className="min-h-screen bg-slate-50">
                <Navbar />
                <main className="flex-1">
                  {children}
                </main>
              </div>
            </AuthGuard>
          </UserProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
