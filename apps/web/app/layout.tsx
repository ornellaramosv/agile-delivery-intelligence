import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Agile Delivery Intelligence",
  description: "ADI doesn't track the work. It explains the delivery.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main">Skip to content</a>
        <div className="shell">
          <header>
            <Link className="project-name" href="/">Agile Delivery Intelligence (ADI)</Link>
            <p>v0.2.0 — Capacity Health</p>
            <nav aria-label="Main navigation">
              <Link href="/sprint-health">Sprint Health</Link>
              <Link href="/delivery-flow">Delivery Flow</Link>
              <Link href="/quality-rework">Quality &amp; Rework</Link>
              <Link href="/capacity-health">Capacity Health</Link>
            </nav>
          </header>
          <main id="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
