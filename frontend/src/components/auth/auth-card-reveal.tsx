"use client";

import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

/**
 * Entrance animation for the auth card: a small spring "pop" (rise + tiny
 * overshoot). Lives in the (auth) layout so every auth page shares one
 * identical entrance. Honors the design-system rule: when the user's OS
 * requests reduced motion, render a plain static wrapper instead.
 */
export function AuthCardReveal({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  const prefersReducedMotion = useReducedMotion();

  if (prefersReducedMotion) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 14, scale: 0.985 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 20, mass: 0.9 }}
    >
      {children}
    </motion.div>
  );
}
