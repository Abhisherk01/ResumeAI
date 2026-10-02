"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { FormError } from "@/components/ui/form-error";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ToastProvider, useToast } from "@/components/ui/toast";
import { useTheme } from "@/themes/theme-provider";
import { THEMES } from "@/themes/themes";

function Gallery() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);

  return (
    <div className="mt-10 space-y-10">
      <section
        aria-labelledby="buttons-heading"
        className="rounded-neu-lg bg-surface p-6 shadow-neu-raised"
      >
        <h2 id="buttons-heading" className="font-semibold">Buttons</h2>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <Button>Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Danger</Button>
          <Button disabled>Disabled</Button>
          <Button
            loading={loading}
            onClick={() => {
              setLoading(true);
              setTimeout(() => setLoading(false), 1500);
            }}
          >
            {loading ? "Saving…" : "Simulate loading"}
          </Button>
        </div>
      </section>

      <section
        aria-labelledby="inputs-heading"
        className="rounded-neu-lg bg-surface p-6 shadow-neu-raised"
      >
        <h2 id="inputs-heading" className="font-semibold">Inputs</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="demo-email">Email</Label>
            <Input id="demo-email" type="email" placeholder="you@example.com" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="demo-invalid">Invalid field</Label>
            <Input
              id="demo-invalid"
              aria-invalid
              aria-describedby="demo-invalid-error"
              defaultValue="not-an-email"
            />
            <FormError id="demo-invalid-error">Enter a valid email address.</FormError>
          </div>
          <div className="space-y-2">
            <Label htmlFor="demo-disabled">Disabled</Label>
            <Input id="demo-disabled" disabled placeholder="Not editable" />
          </div>
        </div>
      </section>

      <section
        aria-labelledby="overlays-heading"
        className="rounded-neu-lg bg-surface p-6 shadow-neu-raised"
      >
        <h2 id="overlays-heading" className="font-semibold">Overlays &amp; feedback</h2>
        <div className="mt-4 flex flex-wrap gap-3">
          <Dialog>
            <DialogTrigger asChild>
              <Button variant="secondary">Open dialog</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Example dialog</DialogTitle>
                <DialogDescription>
                  Focus is trapped here and Escape closes it.
                </DialogDescription>
              </DialogHeader>
              <p className="text-sm text-ink-soft">Dialog content goes here.</p>
              <DialogFooter>
                <DialogClose asChild>
                  <Button variant="secondary">Cancel</Button>
                </DialogClose>
                <DialogClose asChild>
                  <Button>Confirm</Button>
                </DialogClose>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Button
            variant="secondary"
            onClick={() =>
              toast({ title: "Saved", description: "Your resume was stored.", variant: "success" })
            }
          >
            Success toast
          </Button>
          <Button
            variant="secondary"
            onClick={() =>
              toast({ title: "Upload failed", description: "The file could not be read.", variant: "error" })
            }
          >
            Error toast
          </Button>
          <Button variant="ghost" onClick={() => toast({ title: "Heads up", description: "Processing may take a moment." })}>
            Default toast
          </Button>
        </div>
      </section>

      <section
        aria-labelledby="skeleton-heading"
        className="rounded-neu-lg bg-surface p-6 shadow-neu-raised"
      >
        <h2 id="skeleton-heading" className="font-semibold">Skeleton loaders</h2>
        <div className="mt-4 flex items-center gap-4">
          <Skeleton className="h-12 w-12 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        </div>
      </section>
    </div>
  );
}

export default function ComponentGalleryPage() {
  const { theme, setTheme } = useTheme();

  return (
    <main className="mx-auto max-w-4xl p-8">
      <h1 className="text-3xl font-bold tracking-tight">Design system gallery</h1>
      <p className="mt-2 text-ink-soft">
        Step 2 verification page — replaced by the landing page in Step 4.
        Active theme: <span className="font-semibold text-accent">{theme}</span>
      </p>

      <div role="group" aria-label="Select theme" className="mt-6 flex flex-wrap gap-3">
        {THEMES.map((t) => (
          <button
            key={t.id}
            type="button"
            aria-pressed={theme === t.id}
            onClick={() => setTheme(t.id)}
            className={`rounded-neu bg-surface px-4 py-2 text-sm font-medium shadow-neu-raised-sm transition-shadow hover:shadow-neu-raised ${
              theme === t.id ? "shadow-neu-inset text-accent" : "text-ink"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <ToastProvider>
        <Gallery />
      </ToastProvider>
    </main>
  );
}
