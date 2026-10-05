"use client";

import { useAuth } from "@/components/auth/auth-provider";
import { Card } from "@/components/ui/card";

/**
 * The signed-in user's account summary. Reads the user from AuthProvider —
 * seeded by the (app) server gate (D1), so this renders with zero extra
 * API calls. Shows verification state honestly: the badge is derived from
 * the same field the backend reports.
 */
export function AccountCard() {
  const { user } = useAuth();

  if (!user) return null; // unreachable under the (app) gate; defensive

  const memberSince = new Date(user.created_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <Card
      title="Account"
      className="space-y-4"
    >
      <dl className="space-y-3 text-sm">
        <div className="flex items-center justify-between gap-4">
          <dt className="text-ink-soft">Name</dt>
          <dd className="font-medium text-ink">{user.name}</dd>
        </div>
        <div className="flex items-center justify-between gap-4">
          <dt className="text-ink-soft">Email</dt>
          <dd className="font-medium text-ink">{user.email}</dd>
        </div>
        <div className="flex items-center justify-between gap-4">
          <dt className="text-ink-soft">Email verified</dt>
          <dd>
            {user.email_verified ? (
              <span className="rounded-neu bg-base px-2 py-0.5 text-xs font-medium text-success shadow-neu-inset">
                Verified
              </span>
            ) : (
              <span className="rounded-neu bg-base px-2 py-0.5 text-xs font-medium text-warning shadow-neu-inset">
                Not verified
              </span>
            )}
          </dd>
        </div>
        <div className="flex items-center justify-between gap-4">
          <dt className="text-ink-soft">Member since</dt>
          <dd className="font-medium text-ink">{memberSince}</dd>
        </div>
      </dl>
    </Card>
  );
}
