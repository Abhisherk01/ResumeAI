export function PagePlaceholder({
    title,
    description,
    phase,
  }: {
    title: string;
    description: string;
    phase: string;
  }) {
    return (
      <div className="rounded-neu-lg bg-surface p-8 text-center shadow-neu-raised">
        <h1 className="text-xl font-semibold">{title}</h1>
        <p className="mx-auto mt-2 max-w-md text-sm text-ink-soft">{description}</p>
        <p className="mt-4 inline-block rounded-neu bg-base px-3 py-1 text-xs font-medium text-accent shadow-neu-inset">
          Arrives in {phase}
        </p>
      </div>
    );
  }
