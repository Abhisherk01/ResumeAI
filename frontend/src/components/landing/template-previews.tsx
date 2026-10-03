import { Reveal } from "./reveal";

function Bar({
  w,
  tone = "faint",
}: {
  w: string;
  tone?: "faint" | "soft" | "strong" | "accent";
}) {
  const tones = {
    faint: "bg-border",
    soft: "bg-ink-soft",
    strong: "bg-ink",
    accent: "bg-accent",
  } as const;
  return <div className={`h-1.5 rounded-full ${tones[tone]}`} style={{ width: w }} />;
}

const templates = [
  {
    name: "Modern",
    note: "Contemporary typography with a restrained accent edge.",
    preview: (
      <div className="flex h-full gap-3 p-4">
        <div className="w-1.5 rounded-full bg-accent-soft" />
        <div className="flex-1 space-y-2.5">
          <Bar w="55%" tone="strong" />
          <Bar w="35%" tone="accent" />
          <div className="h-2" />
          <Bar w="90%" />
          <Bar w="80%" />
          <Bar w="85%" />
          <div className="h-2" />
          <Bar w="70%" tone="strong" />
          <Bar w="95%" />
          <Bar w="60%" />
        </div>
      </div>
    ),
  },
  {
    name: "Minimal",
    note: "Pure structure, no decoration. Quietly ATS-perfect.",
    preview: (
      <div className="flex h-full flex-col items-center justify-center gap-2.5 p-4">
        <Bar w="45%" tone="strong" />
        <Bar w="30%" />
        <div className="h-2" />
        <Bar w="80%" />
        <Bar w="75%" />
        <Bar w="85%" />
        <Bar w="70%" />
        <div className="h-2" />
        <Bar w="60%" tone="strong" />
        <Bar w="78%" />
        <Bar w="65%" />
      </div>
    ),
  },
  {
    name: "Professional",
    note: "Traditional corporate structure for business and technical roles.",
    preview: (
      <div className="flex h-full flex-col gap-2.5 p-4">
        <div className="rounded-sm bg-border px-2 py-1.5">
          <Bar w="40%" tone="strong" />
        </div>
        <div className="grid flex-1 grid-cols-[1fr_2fr] gap-3 pt-1">
          <div className="space-y-2">
            <Bar w="100%" />
            <Bar w="80%" />
            <Bar w="90%" />
          </div>
          <div className="space-y-2">
            <Bar w="100%" />
            <Bar w="95%" />
            <Bar w="85%" />
            <Bar w="70%" />
          </div>
        </div>
      </div>
    ),
  },
  {
    name: "Developer",
    note: "Built for projects, stacks, and shipping software.",
    preview: (
      <div className="flex h-full flex-col gap-2.5 p-4">
        <div className="flex gap-1.5">
          <span className="h-2 w-2 rounded-full bg-accent" />
          <span className="h-2 w-2 rounded-full bg-border" />
          <span className="h-2 w-2 rounded-full bg-border" />
        </div>
        <Bar w="50%" tone="strong" />
        <div className="flex flex-wrap gap-1 pt-1">
          <span className="h-3 w-10 rounded-sm bg-border" />
          <span className="h-3 w-12 rounded-sm bg-border" />
          <span className="h-3 w-9 rounded-sm bg-border" />
          <span className="h-3 w-11 rounded-sm bg-border" />
          <span className="h-3 w-8 rounded-sm bg-border" />
          <span className="h-3 w-12 rounded-sm bg-border" />
          <span className="h-3 w-10 rounded-sm bg-border" />
        </div>
        <div className="space-y-2 pt-1">
          <Bar w="90%" />
          <Bar w="75%" />
          <Bar w="85%" />
        </div>
      </div>
    ),
  },
];

export function TemplatePreviews() {
  return (
    <section id="templates" className="mx-auto max-w-6xl scroll-mt-24 px-6 py-28 sm:py-36">
      <Reveal>
        <p className="text-xs font-medium uppercase tracking-[0.35em] text-ink-soft">
          Templates
        </p>
        <h2 className="mt-4 max-w-xl font-serif text-3xl font-medium tracking-tight sm:text-4xl">
          Four ways to present the same truth.
        </h2>
        <p className="mt-3 max-w-xl text-sm text-ink-soft">
          Every template renders from your real data. These are structural
          previews — full templates arrive with the editor.
        </p>
      </Reveal>

      <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
        {templates.map(({ name, note, preview }, i) => (
          <Reveal key={name} delay={i * 0.08}>
            <div className="group">
              <div className="aspect-[3/4] overflow-hidden rounded-neu-lg border border-border bg-surface shadow-neu-raised transition-shadow group-hover:shadow-neu-raised-sm">
                {preview}
              </div>
              <h3 className="mt-4 font-serif text-lg font-medium">{name}</h3>
              <p className="mt-1 text-xs leading-relaxed text-ink-soft">{note}</p>
            </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
