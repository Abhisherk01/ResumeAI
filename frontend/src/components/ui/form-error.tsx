import { cn } from "@/lib/utils";

export function FormError({
  id,
  children,
  className,
}: {
  id?: string;
  children?: string;
  className?: string;
}) {
  if (!children) return null;
  return (
    <p id={id} role="alert" className={cn("text-xs font-medium text-error", className)}>
      {children}
    </p>
  );
}
