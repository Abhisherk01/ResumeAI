"use client";

/**
 * Client-side auth state (the interactive half of D1).
 *
 * The server gate (lib/auth/server.ts) decides whether protected pages
 * render at all; this provider carries the ALREADY-RESOLVED user into the
 * client tree via initialUser — no second /me round-trip on first paint.
 */

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";

import { logout as apiLogout, type User } from "@/lib/api/auth";

interface AuthContextValue {
  user: User | null;
  setUser: (user: User | null) => void;
  logout: () => Promise<void>;
  isLoggingOut: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({
  initialUser = null,
  children,
}: {
  initialUser?: User | null;
  children: ReactNode;
}) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(initialUser);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const logout = useCallback(async () => {
    setIsLoggingOut(true);
    try {
      await apiLogout();
    } catch {
      // Deliberate containment, not oversight: the user's intent is to
      // leave, so a failed logout API call (network down, session already
      // revoked server-side) must NOT surface as an error to the caller —
      // the redirect happens regardless and the server gate re-evaluates
      // auth state on the next navigation. Containing the rejection here
      // also means call sites can use `void logout()` safely.
    } finally {
      router.push("/login");
      router.refresh();
      setIsLoggingOut(false);
    }
  }, [router]);

  const value = useMemo(
    () => ({ user, setUser, logout, isLoggingOut }),
    [user, logout, isLoggingOut]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider.");
  }
  return context;
}
