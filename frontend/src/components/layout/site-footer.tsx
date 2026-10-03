import Link from "next/link";

import { Logo } from "./logo";
import { navLinks } from "./site-header";

export function SiteFooter() {
  return (
    <footer className="border-t border-border">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:grid-cols-2 sm:px-6">
        <div>
          <Logo />
          <p className="mt-3 max-w-xs text-sm text-ink-soft">
            AI-powered resume analysis and job matching with transparent,
            explainable scoring.
          </p>
        </div>
        <nav aria-label="Footer">
          <h2 className="text-sm font-semibold text-ink">Product</h2>
          <ul className="mt-3 space-y-2 text-sm text-ink-soft">
            {navLinks.map((link) => (
              <li key={link.href}>
                <Link href={link.href} className="hover:text-ink">
                  {link.label}
                </Link>
              </li>
            ))}
            <li>
              <Link href="/gallery" className="hover:text-ink">
                Design system
              </Link>
            </li>
          </ul>
        </nav>
      </div>
      <div className="border-t border-border px-4 py-4 sm:px-6">
        <p className="mx-auto max-w-6xl text-xs text-ink-soft">
          © {new Date().getFullYear()} ResumeAI — portfolio project. Analysis
          scores and match results are estimates for self-improvement and do not
          represent any employer&apos;s hiring decision or a guarantee of employment.
        </p>
      </div>
    </footer>
  );
}
