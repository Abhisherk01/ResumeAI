import { describe, expect, it } from "vitest";

import { validateResumeFile } from "@/lib/resumes/validation";

function makeFile(name: string, size: number): File {
  return new File(["x".repeat(size)], name);
}

describe("validateResumeFile", () => {
  it("accepts a normal PDF", () => {
    expect(validateResumeFile(makeFile("resume.pdf", 1000))).toBeNull();
  });

  it("accepts a normal DOCX (case-insensitive)", () => {
    expect(validateResumeFile(makeFile("RESUME.DOCX", 1000))).toBeNull();
  });

  it("rejects files over 5 MB", () => {
    const result = validateResumeFile(makeFile("big.pdf", 5 * 1024 * 1024 + 1));
    expect(result?.reason).toContain("5 MB");
  });

  it("accepts a file exactly at 5 MB (boundary: backend rule is >)", () => {
    expect(validateResumeFile(makeFile("exact.pdf", 5 * 1024 * 1024))).toBeNull();
  });

  it("rejects empty files", () => {
    expect(validateResumeFile(makeFile("empty.pdf", 0))?.reason).toContain(
      "empty"
    );
  });

  it("rejects wrong extensions", () => {
    expect(
      validateResumeFile(makeFile("photo.jpg", 1000))?.reason
    ).toContain("PDF and DOCX");
    expect(validateResumeFile(makeFile("noext", 1000))?.reason).toContain(
      "PDF and DOCX"
    );
  });
});
