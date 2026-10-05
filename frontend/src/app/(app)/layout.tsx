import { redirect } from "next/navigation";

import { AuthProvider } from "@/components/auth/auth-provider";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { getCurrentUserServer } from "@/lib/auth/server";

/**
 * Server-side auth gate (D1): the browser's cookies are forwarded to
 * GET /auth/me BEFORE any protected content renders. Not signed in ->
 * redirect to /login, no protected-content flash. The resolved user seeds
 * the client AuthProvider so interactive components need no second /me.
 */
export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getCurrentUserServer();
  if (!user) {
    redirect("/login");
  }

  return (
    <AuthProvider initialUser={user}>
      <div className="min-h-screen bg-base">
        <AppSidebar />
        <div className="lg:pl-64">
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[60] focus:rounded-neu focus:bg-accent focus:px-4 focus:py-2 focus:text-on-accent"
          >
            Skip to content
          </a>
          <main
            id="main-content"
            className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8"
          >
            {children}
          </main>
        </div>
      </div>
    </AuthProvider>
  );
}
