"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react";
import * as ToastPrimitive from "@radix-ui/react-toast";
import { CheckCircle2, Info, X, XCircle } from "lucide-react";

import { cn } from "@/lib/utils";

type ToastVariant = "default" | "success" | "error";

type ToastOptions = {
  title: string;
  description?: string;
  variant?: ToastVariant;
};

type ToastItem = ToastOptions & { id: number; open: boolean };

const ToastContext = createContext<{ toast: (options: ToastOptions) => void } | null>(null);

const REMOVE_DELAY_MS = 200; // let the exit animation finish before unmounting

const iconByVariant: Record<ToastVariant, React.ReactNode> = {
  default: <Info className="h-5 w-5 text-accent-soft-text" aria-hidden="true" />,
  success: <CheckCircle2 className="h-5 w-5 text-success" aria-hidden="true" />,
  error: <XCircle className="h-5 w-5 text-error" aria-hidden="true" />,
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef(1);

  const remove = useCallback((id: number) => {
    setToasts((current) => current.filter((item) => item.id !== id));
  }, []);

  const dismiss = useCallback(
    (id: number) => {
      setToasts((current) =>
        current.map((item) => (item.id === id ? { ...item, open: false } : item))
      );
      window.setTimeout(() => remove(id), REMOVE_DELAY_MS);
    },
    [remove]
  );

  const toast = useCallback((options: ToastOptions) => {
    const id = nextId.current++;
    setToasts((current) => [...current, { ...options, id, open: true }]);
  }, []);

  const value = useMemo(() => ({ toast }), [toast]);

  return (
    <ToastContext.Provider value={value}>
      <ToastPrimitive.Provider swipeDirection="right">
        {children}

        {toasts.map(({ id, title, description, variant = "default", open }) => (
          <ToastPrimitive.Root
            key={id}
            open={open}
            onOpenChange={(isOpen) => {
              if (!isOpen) dismiss(id);
            }}
            className={cn(
              "relative flex items-start gap-3 rounded-neu border border-border bg-surface p-4 shadow-neu-raised",
              "data-[state=open]:animate-in data-[state=closed]:animate-out",
              "data-[state=open]:slide-in-from-right-full data-[state=closed]:slide-out-to-right-full",
              "data-[swipe=end]:animate-out data-[swipe=end]:slide-out-to-right-full"
            )}
          >
            {iconByVariant[variant]}
            <div className="min-w-0">
              <ToastPrimitive.Title className="text-sm font-semibold text-ink">
                {title}
              </ToastPrimitive.Title>
              {description ? (
                <ToastPrimitive.Description className="mt-1 text-sm text-ink-soft">
                  {description}
                </ToastPrimitive.Description>
              ) : null}
            </div>
            <ToastPrimitive.Close
              aria-label="Dismiss notification"
              className="absolute right-3 top-3 rounded-md p-1 text-ink-soft transition-colors hover:text-ink"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </ToastPrimitive.Close>
          </ToastPrimitive.Root>
        ))}

        <ToastPrimitive.Viewport className="fixed bottom-4 right-4 z-[100] flex w-full max-w-sm flex-col gap-3 outline-none" />
      </ToastPrimitive.Provider>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used within <ToastProvider>");
  return context;
}
