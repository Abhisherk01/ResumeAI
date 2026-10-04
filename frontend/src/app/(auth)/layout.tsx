import Link from "next/link";

import { AuthCardReveal } from "@/components/auth/auth-card-reveal";
import { Logo } from "@/components/layout/logo";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-base px-4 py-12">
      <Logo className="mb-8" />
      <AuthCardReveal className="w-full max-w-md">
        <div className="rounded-neu-lg bg-surface p-6 shadow-neu-raised sm:p-8">
          {children}
        </div>
      </AuthCardReveal>
      <p className="mt-6 text-sm text-ink-soft">
        <Link href="/" className="font-medium text-accent hover:underline">
          Back to home
        </Link>
      </p>
    </div>
  );
}
