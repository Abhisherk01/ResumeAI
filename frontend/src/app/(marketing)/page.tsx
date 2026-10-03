import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function LandingPlaceholderPage() {
  return (
    <section className="mx-auto max-w-4xl px-4 py-24 text-center sm:py-32">
      <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
        Your resume, understood.
      </h1>
      <p className="mx-auto mt-4 max-w-2xl text-lg text-ink-soft">
        ResumeAI analyzes your resume, matches it against job descriptions, and
        helps you close the gap — with transparent scoring, not black-box verdicts.
      </p>
      <div className="mt-8 flex flex-wrap justify-center gap-4">
        <Link href="/register" className={cn(buttonVariants({ size: "lg" }))}>
          Get started free
        </Link>
        <Link href="/gallery" className={cn(buttonVariants({ variant: "secondary", size: "lg" }))}>
          View design system
        </Link>
      </div>
    </section>
  );
}
