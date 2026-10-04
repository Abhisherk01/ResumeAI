/**
 * Typed functions for the seven backend auth endpoints (Phase 3 Step 4/6).
 * One function per endpoint — components never build URLs or parse
 * envelopes; errors surface as ApiError from the shared client.
 */

import { apiFetch } from "@/lib/api/client";
import type {
  ForgotPasswordInput,
  LoginInput,
  RegisterInput,
  ResetPasswordPayload,
  VerifyEmailInput,
} from "@/lib/auth/schemas";

/** Mirrors backend UserResponse — note what's absent: no password material. */
export interface User {
  id: string;
  email: string;
  name: string;
  email_verified: boolean;
  created_at: string;
}

interface MessageResponse {
  message: string;
}

export async function register(input: RegisterInput): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/auth/register", {
    method: "POST",
    body: input,
  });
}

export async function verifyEmail(input: VerifyEmailInput): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/auth/verify-email", {
    method: "POST",
    body: input,
  });
}

export async function login(input: LoginInput): Promise<User> {
  return apiFetch<User>("/auth/login", { method: "POST", body: input });
}

/** 204 No Content on success — apiFetch returns undefined. */
export async function logout(): Promise<void> {
  return apiFetch<void>("/auth/logout", { method: "POST" });
}

export async function requestPasswordReset(
  input: ForgotPasswordInput
): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/auth/password-reset", {
    method: "POST",
    body: input,
  });
}

export async function confirmPasswordReset(
  payload: ResetPasswordPayload
): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/auth/password-reset/confirm", {
    method: "POST",
    body: payload,
  });
}

export async function getCurrentUser(): Promise<User> {
  return apiFetch<User>("/auth/me");
}
