import { describe, expect, it } from "vitest";

import {
  forgotPasswordSchema,
  loginSchema,
  registerSchema,
  resetPasswordSchema,
} from "@/lib/auth/schemas";

describe("registerSchema (mirrors backend Decision D)", () => {
  it("rejects a 7-character password and accepts 8", () => {
    expect(
      registerSchema.safeParse({ email: "a@b.co", password: "1234567", name: "A" })
        .success
    ).toBe(false);
    expect(
      registerSchema.safeParse({ email: "a@b.co", password: "12345678", name: "A" })
        .success
    ).toBe(true);
  });

  it("accepts a 128-character password and rejects 129", () => {
    const ok = "x".repeat(128);
    const tooLong = "x".repeat(129);
    expect(
      registerSchema.safeParse({ email: "a@b.co", password: ok, name: "A" }).success
    ).toBe(true);
    expect(
      registerSchema.safeParse({ email: "a@b.co", password: tooLong, name: "A" })
        .success
    ).toBe(false);
  });

  it("rejects blank and whitespace-only names", () => {
    expect(
      registerSchema.safeParse({ email: "a@b.co", password: "12345678", name: "   " })
        .success
    ).toBe(false);
  });

  it("trims the name before validating length", () => {
    const result = registerSchema.parse({
      email: "a@b.co",
      password: "12345678",
      name: "  Ada Lovelace  ",
    });
    expect(result.name).toBe("Ada Lovelace");
  });

  it("rejects malformed emails", () => {
    expect(
      registerSchema.safeParse({ email: "not-an-email", password: "12345678", name: "A" })
        .success
    ).toBe(false);
  });
});

describe("loginSchema", () => {
  it("accepts any non-empty password (does not leak the policy)", () => {
    expect(
      loginSchema.safeParse({ email: "a@b.co", password: "x" }).success
    ).toBe(true);
    expect(
      loginSchema.safeParse({ email: "a@b.co", password: "" }).success
    ).toBe(false);
  });
});

describe("forgotPasswordSchema", () => {
  it("requires a valid email", () => {
    expect(forgotPasswordSchema.safeParse({ email: "a@b.co" }).success).toBe(true);
    expect(forgotPasswordSchema.safeParse({ email: "nope" }).success).toBe(false);
  });
});

describe("resetPasswordSchema", () => {
  it("rejects when the confirmation does not match", () => {
    const result = resetPasswordSchema.safeParse({
      token: "t",
      new_password: "12345678",
      confirmPassword: "87654321",
    });
    expect(result.success).toBe(false);
  });

  it("accepts a matching confirmation", () => {
    expect(
      resetPasswordSchema.safeParse({
        token: "t",
        new_password: "12345678",
        confirmPassword: "12345678",
      }).success
    ).toBe(true);
  });
});
