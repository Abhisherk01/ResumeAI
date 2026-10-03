import { Gauge, History, PenLine, Puzzle, ShieldCheck, Sparkles } from "lucide-react";

import { Reveal } from "./reveal";

const features = [
  {
    icon: Gauge,
    title: "Explainable analysis",
    text: "Every category score is broken down and justified. You always know why a number moved — no black-box verdicts.",
  },
  {
    icon: Puzzle,
    title: "Honest job matching",
    text: "Matched, partial, and missing skills against any job description — deterministic matching first, semantics where they help.",
  },
  {
    icon: PenLine,
    title: "An editor that respects your words",
    text: "Correct extracted data, reorder sections, choose a template — and export a clean, ATS-readable PDF.",
  },
  {
    icon: ShieldCheck,
    title: "Security by default",
    text: "Argon2-hashed passwords, HTTP-only session cookies, and strict resource ownership. Your documents belong to you.",
  },
  {
    icon: History,
    title: "History that stays yours",
    text: "Every analysis and match report is saved to your account, paginated, and deletable at any time.",
  },
  {
    icon: Sparkles,
    title: "Transparent AI use",
    text: "AI suggestions are clearly labeled, evidence-based, and always editable. Deterministic scoring stays separate from AI text.",
  },
];

export function Features() {
  return (
    <section id="features" className="scroll-mt-24 bg-surface py-28 sm:py-36">
      <div className="mx-auto max-w-6xl px-6">
        <Reveal>
          <p className="text-xs font-medium uppercase tracking-[0.35em] text-ink-soft">
            Capabilities
          </p>
          <h2 className="mt-4 max-w-xl font-serif text-3xl font-medium tracking-tight sm:text-4xl">
            Everything essential. Nothing decorative.
          </h2>
        </Reveal>

        <div className="mt-16 grid gap-x-10 gap-y-14 sm:grid-cols-2 lg:grid-cols-3">
          {features.map(({ icon: Icon, title, text }, i) => (
            <Reveal key={title} delay={(i % 3) * 0.08}>
              <Icon className="h-5 w-5 text-accent" aria-hidden="true" />
              <h3 className="mt-4 font-serif text-lg font-medium">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-soft">{text}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
