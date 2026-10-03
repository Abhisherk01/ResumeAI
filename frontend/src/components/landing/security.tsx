import { FileLock, KeyRound, ShieldCheck, Trash2 } from "lucide-react";

import { Reveal } from "./reveal";

const commitments = [
  {
    icon: KeyRound,
    title: "Passwords are never stored",
    text: "Only Argon2id hashes — the current standard for password storage.",
  },
  {
    icon: ShieldCheck,
    title: "Sessions you control",
    text: "HTTP-only cookies, server-side sessions, CSRF protection. Nothing sensitive lives in your browser's storage.",
  },
  {
    icon: FileLock,
    title: "Strict data ownership",
    text: "Every request verifies that a resource belongs to you. Not probably yours — verifiably yours.",
  },
  {
    icon: Trash2,
    title: "Real deletion",
    text: "Delete any resume, report, or your entire account — data is removed, not hidden.",
  },
];

export function Security() {
  return (
    <section className="bg-surface py-28 sm:py-36">
      <div className="mx-auto max-w-6xl px-6">
        <Reveal>
          <p className="text-xs font-medium uppercase tracking-[0.35em] text-ink-soft">
            Security &amp; privacy
          </p>
          <h2 className="mt-4 max-w-xl font-serif text-3xl font-medium tracking-tight sm:text-4xl">
            Quiet infrastructure, visible promises.
          </h2>
        </Reveal>

        <div className="mt-16 grid gap-x-10 gap-y-12 sm:grid-cols-2">
          {commitments.map(({ icon: Icon, title, text }, i) => (
            <Reveal key={title} delay={(i % 2) * 0.08}>
              <div className="flex gap-4">
                <Icon className="mt-0.5 h-5 w-5 shrink-0 text-accent" aria-hidden="true" />
                <div>
                  <h3 className="font-serif text-lg font-medium">{title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">{text}</p>
                </div>
              </div>
            </Reveal>
          ))}
        </div>

        <Reveal delay={0.1}>
          <p className="mt-14 max-w-2xl text-xs leading-relaxed text-ink-soft">
            Transparency note: resume content you submit is processed by our
            servers and by an external AI provider to generate analysis and
            suggestions. This is disclosed in the product and privacy policy,
            and you can delete your data at any time.
          </p>
        </Reveal>
      </div>
    </section>
  );
}
