import { FileSearch, ListChecks, Sparkles, Target } from "lucide-react";

import { Reveal } from "./reveal";

const steps = [
  {
    icon: FileSearch,
    title: "Upload",
    text: "Your resume, as PDF or DOCX — validated and parsed in seconds.",
  },
  {
    icon: ListChecks,
    title: "Review",
    text: "Confirm what the parser extracted. You stay in control of your data.",
  },
  {
    icon: Target,
    title: "Match",
    text: "Paste any job description. See matched, partial, and missing skills.",
  },
  {
    icon: Sparkles,
    title: "Improve",
    text: "Evidence-based suggestions, a refined resume, and a polished PDF export.",
  },
];

export function HowItWorks() {
  return (
    <section
      id="how-it-works"
      className="mx-auto max-w-6xl scroll-mt-24 px-6 py-28 sm:py-36"
    >
      <Reveal>
        <p className="text-xs font-medium uppercase tracking-[0.35em] text-ink-soft">
          The process
        </p>
        <h2 className="mt-4 max-w-xl font-serif text-3xl font-medium tracking-tight sm:text-4xl">
          Four quiet steps. No noise.
        </h2>
      </Reveal>

      <div className="mt-16 grid gap-x-8 gap-y-12 sm:grid-cols-2 lg:grid-cols-4">
        {steps.map(({ icon: Icon, title, text }, i) => (
          <Reveal key={title} delay={i * 0.08}>
            <div className="flex h-full flex-col">
              <span className="flex h-11 w-11 items-center justify-center rounded-neu bg-surface text-accent shadow-neu-raised-sm">
                <Icon className="h-5 w-5" aria-hidden="true" />
              </span>
              <p className="mt-5 text-xs font-medium tracking-widest text-ink-soft">0{i + 1}</p>
              <h3 className="mt-1 font-serif text-xl font-medium">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-soft">{text}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
