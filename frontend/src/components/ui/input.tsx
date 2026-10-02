import { forwardRef, type InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export type InputProps = InputHTMLAttributes<HTMLInputElement>;

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", ...props }, ref) => (
    <input
      ref={ref}
      type={type}
      className={cn(
        "h-11 w-full rounded-neu bg-base px-4 text-sm text-ink shadow-neu-inset",
        "placeholder:text-ink-soft disabled:cursor-not-allowed disabled:opacity-50",
        "aria-[invalid=true]:ring-1 aria-[invalid=true]:ring-error",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";
