import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kisaan Dost — Operations Dashboard",
  description: "Admin and advisor panels for the Kisaan Dost crop-risk platform.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
