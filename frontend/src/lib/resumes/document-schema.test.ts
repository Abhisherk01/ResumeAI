import { describe, expect, it } from "vitest";

import {
  contentFromWire,
  contentToWire,
  emptyEducationItemForm,
  emptyExperienceItemForm,
  emptyProjectItemForm,
  emptyResumeDocument,
  emptyResumeDocumentForm,
  resumeDocumentFormSchema,
  resumeDocumentSaveSchema,
  resumeDocumentSchema,
} from "@/lib/resumes/document-schema";

const fullDocument = {
  basics: {
    name: "Ada Lovelace",
    email: "ada@example.com",
    phone: "+1 555 0100",
    location: "London",
    links: ["https://github.com/ada"],
  },
  summary: "Analytical engineer.",
  experience: [
    {
      title: "Engineer",
      company: "Analytical Engines Ltd",
      start: "1843",
      end: "Present",
      bullets: ["Wrote the first algorithm."],
    },
  ],
  education: [],
  skills: ["Python", "SQL"],
  projects: [],
};

describe("resume document schema (P8-4 mirror)", () => {
  it("parses an empty object into the complete canonical shape (P8-3)", () => {
    expect(emptyResumeDocument()).toEqual({
      basics: { name: "", email: "", phone: "", location: "", links: [] },
      summary: "",
      experience: [],
      education: [],
      skills: [],
      projects: [],
    });
  });

  it("roundtrips a full document losslessly", () => {
    expect(resumeDocumentSchema.parse(fullDocument)).toEqual(fullDocument);
  });

  it("rejects unknown top-level keys (.strict mirrors extra=forbid)", () => {
    const bad = { ...fullDocument, experiences: [] };
    expect(() => resumeDocumentSchema.parse(bad)).toThrow();
  });

  it("rejects unknown keys inside experience items", () => {
    const bad = {
      experience: [{ ...fullDocument.experience[0], job_title: "typo" }],
    };
    expect(() => resumeDocumentSchema.parse(bad)).toThrow();
  });

  it("rejects an over-cap summary", () => {
    const bad = { ...fullDocument, summary: "x".repeat(2001) };
    expect(() => resumeDocumentSchema.parse(bad)).toThrow();
  });

  it("rejects more than 40 skills", () => {
    const bad = { ...fullDocument, skills: Array.from({ length: 41 }, () => "s") };
    expect(() => resumeDocumentSchema.parse(bad)).toThrow();
  });

  it("rejects an unknown template id in the save payload", () => {
    const bad = { template_id: "fancy", content: fullDocument };
    expect(() => resumeDocumentSaveSchema.parse(bad)).toThrow();
  });

  it("rejects an unknown accent in the save payload", () => {
    const bad = { accent: "chartreuse", content: fullDocument };
    expect(() => resumeDocumentSaveSchema.parse(bad)).toThrow();
  });

  it("defaults the save payload to classic/blue", () => {
    const parsed = resumeDocumentSaveSchema.parse({ content: fullDocument });
    expect(parsed.template_id).toBe("classic");
    expect(parsed.accent).toBe("blue");
  });
});

describe("form-state mapping (D14-1)", () => {
  const fullForm = contentFromWire(fullDocument);

  it("boxes every primitive array element on the way in", () => {
    expect(fullForm.skills).toEqual([{ value: "Python" }, { value: "SQL" }]);
    expect(fullForm.basics.links).toEqual([
      { value: "https://github.com/ada" },
    ]);
    expect(fullForm.experience[0].bullets).toEqual([
      { value: "Wrote the first algorithm." },
    ]);
    // Object sections pass through unboxed:
    expect(fullForm.experience[0].title).toBe("Engineer");
    expect(fullForm.experience[0].company).toBe("Analytical Engines Ltd");
  });

  it("contentFromWire of the empty wire document is the canonical empty form", () => {
    expect(contentFromWire(emptyResumeDocument())).toEqual(
      emptyResumeDocumentForm()
    );
  });

  it("contentToWire is the exact inverse of contentFromWire (full roundtrip)", () => {
    expect(contentToWire(fullForm)).toEqual(fullDocument);
  });

  it("THE HAZARD PIN: contentToWire output parses through the SAVE schema", () => {
    // extra="forbid" on the backend contract means a leaked {value} box
    // would be a loud parse error here - never a silent 422 in production.
    expect(() =>
      resumeDocumentSaveSchema.parse({
        template_id: "classic",
        accent: "blue",
        content: contentToWire(fullForm),
      })
    ).not.toThrow();
  });

  it("contentToWire of the empty form equals the canonical empty wire document", () => {
    expect(contentToWire(emptyResumeDocumentForm())).toEqual(
      emptyResumeDocument()
    );
  });

  it("the form schema accepts fully populated form state", () => {
    expect(() => resumeDocumentFormSchema.parse(fullForm)).not.toThrow();
  });

  it("the form schema rejects an over-cap boxed skill", () => {
    const bad = { ...fullForm, skills: [{ value: "x".repeat(101) }] };
    expect(() => resumeDocumentFormSchema.parse(bad)).toThrow();
  });

  it("the form schema rejects an unknown key inside a boxed skill (strict)", () => {
    const bad = { ...fullForm, skills: [{ value: "Python", text: "extra" }] };
    expect(() => resumeDocumentFormSchema.parse(bad)).toThrow();
  });

  it("the form schema rejects an over-cap boxed bullet", () => {
    const bad = {
      ...fullForm,
      experience: [
        { ...fullForm.experience[0], bullets: [{ value: "x".repeat(501) }] },
      ],
    };
    expect(() => resumeDocumentFormSchema.parse(bad)).toThrow();
  });

  it("empty item helpers produce complete form-shaped append payloads", () => {
    expect(emptyExperienceItemForm()).toEqual({
      title: "",
      company: "",
      start: "",
      end: "",
      bullets: [],
    });
    expect(emptyEducationItemForm()).toEqual({
      school: "",
      degree: "",
      start: "",
      end: "",
      bullets: [],
    });
    expect(emptyProjectItemForm()).toEqual({
      name: "",
      url: "",
      bullets: [],
    });
    // Every append payload parses through the form schema:
    expect(() =>
      resumeDocumentFormSchema.parse({
        ...emptyResumeDocumentForm(),
        experience: [emptyExperienceItemForm()],
        education: [emptyEducationItemForm()],
        projects: [emptyProjectItemForm()],
      })
    ).not.toThrow();
  });
});
