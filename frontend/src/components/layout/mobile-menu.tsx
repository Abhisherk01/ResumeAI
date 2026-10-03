"use client";

import Link from "next/link";
import { useState } from "react";
import { Menu } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

type NavLink = { href: string; label: string };

export function MobileMenu({ links }: { links: NavLink[] }) {
  const [open, setOpen] = useState(false);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button
          type="button"
          aria-label="Open navigation menu"
          className={cn(buttonVariants({ variant: "secondary", size: "icon" }), "md:hidden")}
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </button>
      </DialogTrigger>
      <DialogContent>
        <DialogTitle>Menu</DialogTitle>
        <nav aria-label="Mobile" className="mt-4 flex flex-col gap-1">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setOpen(false)}
              className="rounded-neu px-3 py-2.5 text-sm font-medium text-ink-soft hover:text-ink"
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="mt-6 flex flex-col gap-3">
          <Link
            href="/login"
            onClick={() => setOpen(false)}
            className={cn(buttonVariants({ variant: "secondary" }), "w-full")}
          >
            Sign in
          </Link>
          <Link
            href="/register"
            onClick={() => setOpen(false)}
            className={cn(buttonVariants(), "w-full")}
          >
            Get started
          </Link>
        </div>
      </DialogContent>
    </Dialog>
  );
}
