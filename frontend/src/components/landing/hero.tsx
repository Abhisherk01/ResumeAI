import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Reveal } from "./reveal";

export function Hero() {
  return (
    <section className="relative flex min-h-[85vh] flex-col items-center justify-center px-6 text-center">
      <Reveal>
        <p className="text-xs font-medium uppercase tracking-[0.35em] text-ink-soft">
          Resume Analysis · Job Matching
        </p>
      </Reveal>

      <Reveal delay={0.1}>
        <h1 className="mt-6 max-w-3xl font-serif text-5xl font-medium leading-[1.1] tracking-tight text-ink sm:text-6xl lg:text-7xl">
          Your resume,
          <br />
          quietly understood.
        </h1>
      </Reveal>

      <Reveal delay={0.2}>
        <p className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-ink-soft">
          Transparent, explainable analysis — and a clear view of what stands
          between you and the role you want.
        </p>
      </Reveal>

      <Reveal delay={0.3}>
        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row">
          <Link href="/register" className={cn(buttonVariants({ size: "lg" }), "min-w-44")}>
            Begin analysis
          </Link>
          <Link
            href="/#how-it-works"
            className={cn(buttonVariants({ variant: "secondary", size: "lg" }), "min-w-44")}
          >
            See how it works
          </Link>
        </div>
      </Reveal>

      <Reveal delay={0.45}>
        <p className="mt-14 text-xs tracking-wide text-ink-soft">
          No credit card required · Your documents stay private
        </p>
        <p className="mt-2 text-[11px] text-ink-soft">
          Scores are self-improvement estimates — not employer decisions or ATS verdicts.
        </p>
      </Reveal>
    </section>
  );
}
