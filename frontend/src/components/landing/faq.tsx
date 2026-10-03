import { ChevronDown } from "lucide-react";

import { Reveal } from "./reveal";

const faqs = [
  {
    q: "Is the score a real ATS verdict?",
    a: "No — and we won't pretend otherwise. The score is a transparent, explainable estimate built from documented criteria like completeness, readability, and keyword coverage. It's a self-improvement tool, not a simulation of any employer's system.",
  },
  {
    q: "Does this guarantee interviews or jobs?",
    a: "No. ResumeAI helps you present your real experience more clearly and close skill gaps. Hiring decisions belong to employers, and no tool can promise outcomes.",
  },
  {
    q: "What happens to my resume data?",
    a: "Your documents are stored in your account, visible only to you, and deletable at any time. To generate suggestions, resume content is processed by an external AI provider — disclosed up front, and the AI is never allowed to invent qualifications you don't have.",
  },
  {
    q: "Can the AI invent experience or skills?",
    a: "No. Suggestions must cite evidence from your resume, AI-generated text is clearly labeled and editable before you apply it, and deterministic scoring is computed by fixed algorithms — separate from any AI output.",
  },
  {
    q: "Is it free?",
    a: "The core workflow — upload, analysis, matching, and export — runs on free tiers of the underlying services. You may see rate limits, never a bill.",
  },
];

export function Faq() {
  return (
    <section id="faq" className="mx-auto max-w-3xl scroll-mt-24 px-6 py-28 sm:py-36">
      <Reveal>
        <p className="text-xs font-medium uppercase tracking-[0.35em] text-ink-soft">
          Questions
        </p>
        <h2 className="mt-4 font-serif text-3xl font-medium tracking-tight sm:text-4xl">
          Asked honestly, answered directly.
        </h2>
      </Reveal>

      <div className="mt-14 divide-y divide-border">
        {faqs.map(({ q, a }, i) => (
          <Reveal key={q} delay={i * 0.05}>
            <details className="group py-5">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-medium text-ink [&::-webkit-details-marker]:hidden">
                {q}
                <ChevronDown
                  className="h-4 w-4 shrink-0 text-ink-soft transition-transform duration-200 group-open:rotate-180"
                  aria-hidden="true"
                />
              </summary>
              <p className="mt-3 max-w-2xl text-sm leading-relaxed text-ink-soft">{a}</p>
            </details>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
