"use client";

/**
 * Sessions manager (Phase 10, D23): every live session, newest first, with
 * the CURRENT one flagged and non-revocable (the backend refuses it with
 * 409 - the UI hides the button instead, defense in depth). Every action
 * refetches the list; revoke-others surfaces the backend's count message.
 * The list can never be empty for a signed-in user (their current session
 * always exists), so only fetch errors are error states.
 */

import { useCallback, useEffect, useState } from "react";

import {
  describeApiError,
  describeUnknownError,
} from "@/components/auth/api-error-message";
import { FormError } from "@/components/ui/form-error";
import { ApiError } from "@/lib/api/client";
import {
  listSessions,
  revokeOtherSessions,
  revokeSession,
  type SessionInfo,
} from "@/lib/api/auth";
import { Button } from "@/components/ui/button";

export function SessionsSection() {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [othersBusy, setOthersBusy] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      setSessions(await listSessions());
    } catch (err) {
      setError(
        err instanceof ApiError ? describeApiError(err) : describeUnknownError()
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleRevoke(sessionId: string) {
    setActionError(null);
    setNotice(null);
    setBusyId(sessionId);
    try {
      await revokeSession(sessionId);
      await load();
    } catch (err) {
      setActionError(
        err instanceof ApiError ? describeApiError(err) : describeUnknownError()
      );
    } finally {
      setBusyId(null);
    }
  }

  async function handleRevokeOthers() {
    setActionError(null);
    setNotice(null);
    setOthersBusy(true);
    try {
      const result = await revokeOtherSessions();
      setNotice(result.message);
      await load();
    } catch (err) {
      setActionError(
        err instanceof ApiError ? describeApiError(err) : describeUnknownError()
      );
    } finally {
      setOthersBusy(false);
    }
  }

  return (
    <form
      onSubmit={(event) => event.preventDefault()}
      noValidate
      className="space-y-4"
    >
      <div className="space-y-1">
        <h2 className="text-base font-semibold">Active sessions</h2>
        <p className="text-sm text-ink-soft">
          Devices signed in to your account. Signing out a device does not
          affect this one.
        </p>
      </div>
      <FormError>{error ?? undefined}</FormError>
      {loading ? (
        <p role="status" className="text-sm text-ink-soft">
          Loading sessions...
        </p>
      ) : (
        <>
          <FormError>{actionError ?? undefined}</FormError>
          {notice && (
            <p role="status" className="text-sm text-success">
              {notice}
            </p>
          )}
          <ul className="space-y-2">
            {sessions.map((session) => (
              <li
                key={session.id}
                className="flex items-center justify-between gap-3 rounded-neu bg-base px-4 py-3 shadow-neu-inset"
              >
                <div className="space-y-0.5">
                  <p className="text-sm font-medium text-ink">
                    Signed in {new Date(session.created_at).toLocaleDateString()}
                    {session.is_current && (
                      <span className="ml-2 text-xs font-normal text-success">
                        (this device)
                      </span>
                    )}
                  </p>
                  <p className="text-xs text-ink-soft">
                    Expires {new Date(session.expires_at).toLocaleDateString()}
                  </p>
                </div>
                {!session.is_current && (
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    loading={busyId === session.id}
                    onClick={() => void handleRevoke(session.id)}
                  >
                    Sign out
                  </Button>
                )}
              </li>
            ))}
          </ul>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            loading={othersBusy}
            onClick={() => void handleRevokeOthers()}
          >
            Sign out other devices
          </Button>
        </>
      )}
    </form>
  );
}
