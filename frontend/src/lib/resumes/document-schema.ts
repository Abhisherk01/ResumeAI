/**
 * Zod mirror of the backend's resume document contract (P8-4) - the ONE
 * frontend source of truth for the editor form, exactly as
 * backend/app/schemas/resume_document.py is the backend's.
 *
 * The BACKEND REMAINS THE AUTHORITY: this layer exists for instant field
 * feedback and typed form state; the backend re-validates every save.
 * .strict() here mirrors extra="forbid" there - same posture.
 *
 * Keep in sync (by comment, deliberately):
 * - field caps  -> backend Field(max_length=...) values
 * - template/accent ids -> backend Literal[...] sets in
 *   schemas/resume_document.py (the 4b pickers import THESE constants)
 * All fields default to empty (P8-3): the editor starts with an empty
 * structured document; there is no auto-import from raw_text.
 *
 * FORM-STATE vs WIRE (D14-1, evidence-based): RHF 7.53's useFieldArray
 * deterministically fails to render a SECOND append into a primitive
 * (string[]) array, while object arrays multi-append correctly (pinned
 * by the multi-append regression test). Form state therefore boxes every
 * field-array element as {value: string}; the pure mappers below convert
 * at the API boundary:
 * - contentFromWire: API content -> form state (on load)
 * - contentToWire:   form state  -> API content (before PUT)
 * The wire schema stays the ONE backend contract; contentToWire's output
 * parsing through resumeDocumentSaveSchema is TESTED - extra="forbid"
 * turns any leaked box into a loud failure in tests, not a silent 422
 * in production.
 */

import { z } from "zod";

export const RESUME_TEMPLATE_IDS = [
  "classic",
  "modern",
  "compact",
  "creative",
] as const;
export const RESUME_ACCENT_IDS = [
  "blue",
  "teal",
  "green",
  "amber",
  "rose",
  "violet",
] as const;

export const resumeTemplateIdSchema = z.enum(RESUME_TEMPLATE_IDS);
export const resumeAccentSchema = z.enum(RESUME_ACCENT_IDS);

export type ResumeTemplateId = z.infer<typeof resumeTemplateIdSchema>;
export type ResumeAccent = z.infer<typeof resumeAccentSchema>;

/** Caps mirror backend Field limits (see module docstring). */
export const DOCUMENT_LIMITS = {
  name: 200,
  email: 254,
  phone: 40,
  location: 120,
  link: 500,
  links: 10,
  summary: 2000,
  itemField: 200,
  date: 50,
  bullet: 500,
  bullets: 20,
  skill: 100,
  skills: 40,
  url: 500,
  experience: 15,
  education: 15,
  projects: 15,
} as const;

const bulletSchema = z.string().max(DOCUMENT_LIMITS.bullet);
const bulletsSchema = z
  .array(bulletSchema)
  .max(DOCUMENT_LIMITS.bullets)
  .default([]);

export const resumeBasicsSchema = z
  .object({
    name: z.string().max(DOCUMENT_LIMITS.name).default(""),
    email: z.string().max(DOCUMENT_LIMITS.email).default(""),
    phone: z.string().max(DOCUMENT_LIMITS.phone).default(""),
    location: z.string().max(DOCUMENT_LIMITS.location).default(""),
    links: z
      .array(z.string().max(DOCUMENT_LIMITS.link))
      .max(DOCUMENT_LIMITS.links)
      .default([]),
  })
  .strict();

export const experienceItemSchema = z
  .object({
    title: z.string().max(DOCUMENT_LIMITS.itemField).default(""),
    company: z.string().max(DOCUMENT_LIMITS.itemField).default(""),
    start: z.string().max(DOCUMENT_LIMITS.date).default(""),
    end: z.string().max(DOCUMENT_LIMITS.date).default(""),
    bullets: bulletsSchema,
  })
  .strict();

export const educationItemSchema = z
  .object({
    school: z.string().max(DOCUMENT_LIMITS.itemField).default(""),
    degree: z.string().max(DOCUMENT_LIMITS.itemField).default(""),
    start: z.string().max(DOCUMENT_LIMITS.date).default(""),
    end: z.string().max(DOCUMENT_LIMITS.date).default(""),
    bullets: bulletsSchema,
  })
  .strict();

export const projectItemSchema = z
  .object({
    name: z.string().max(DOCUMENT_LIMITS.itemField).default(""),
    url: z.string().max(DOCUMENT_LIMITS.url).default(""),
    bullets: bulletsSchema,
  })
  .strict();

export const resumeDocumentSchema = z
  .object({
    basics: resumeBasicsSchema.default(resumeBasicsSchema.parse({})),
    summary: z.string().max(DOCUMENT_LIMITS.summary).default(""),
    experience: z
      .array(experienceItemSchema)
      .max(DOCUMENT_LIMITS.experience)
      .default([]),
    education: z
      .array(educationItemSchema)
      .max(DOCUMENT_LIMITS.education)
      .default([]),
    skills: z
      .array(z.string().max(DOCUMENT_LIMITS.skill))
      .max(DOCUMENT_LIMITS.skills)
      .default([]),
    projects: z
      .array(projectItemSchema)
      .max(DOCUMENT_LIMITS.projects)
      .default([]),
  })
  .strict();

export type ResumeDocumentValues = z.infer<typeof resumeDocumentSchema>;
export type ExperienceItemValues = z.infer<typeof experienceItemSchema>;
export type EducationItemValues = z.infer<typeof educationItemSchema>;
export type ProjectItemValues = z.infer<typeof projectItemSchema>;

/** Request payload for PUT /resumes/{id}/document (mirrors the backend's
 * ResumeDocumentSave: template/accent travel NEXT TO content, P8-2). */
export const resumeDocumentSaveSchema = z
  .object({
    template_id: resumeTemplateIdSchema.default("classic"),
    accent: resumeAccentSchema.default("blue"),
    content: resumeDocumentSchema,
  })
  .strict();

export type ResumeDocumentSaveValues = z.infer<typeof resumeDocumentSaveSchema>;

/** The canonical empty document (P8-3) - derived from the schema itself so
 * the two can never drift. */
export function emptyResumeDocument(): ResumeDocumentValues {
  return resumeDocumentSchema.parse({});
}

// ============================================================================
// FORM STATE (D14-1): same caps (shared DOCUMENT_LIMITS - cap drift is
// impossible), same keys, but every field-array element is boxed. Pinned
// to the wire schemas by the roundtrip tests in document-schema.test.ts.
// ============================================================================

const bulletBoxSchema = z
  .object({ value: z.string().max(DOCUMENT_LIMITS.bullet).default("") })
  .strict();
const linkBoxSchema = z
  .object({ value: z.string().max(DOCUMENT_LIMITS.link).default("") })
  .strict();
const skillBoxSchema = z
  .object({ value: z.string().max(DOCUMENT_LIMITS.skill).default("") })
  .strict();

export const resumeBasicsFormSchema = z
  .object({
    name: z.string().max(DOCUMENT_LIMITS.name).default(""),
    email: z.string().max(DOCUMENT_LIMITS.email).default(""),
    phone: z.string().max(DOCUMENT_LIMITS.phone).default(""),
    location: z.string().max(DOCUMENT_LIMITS.location).default(""),
    links: z.array(linkBoxSchema).max(DOCUMENT_LIMITS.links).default([]),
  })
  .strict();

export const experienceItemFormSchema = z
  .object({
    title: z.string().max(DOCUMENT_LIMITS.itemField).default(""),
    company: z.string().max(DOCUMENT_LIMITS.itemField).default(""),
    start: z.string().max(DOCUMENT_LIMITS.date).default(""),
    end: z.string().max(DOCUMENT_LIMITS.date).default(""),
    bullets: z.array(bulletBoxSchema).max(DOCUMENT_LIMITS.bullets).default([]),
  })
  .strict();

export const educationItemFormSchema = z
  .object({
    school: z.string().max(DOCUMENT_LIMITS.itemField).default(""),
    degree: z.string().max(DOCUMENT_LIMITS.itemField).default(""),
    start: z.string().max(DOCUMENT_LIMITS.date).default(""),
    end: z.string().max(DOCUMENT_LIMITS.date).default(""),
    bullets: z.array(bulletBoxSchema).max(DOCUMENT_LIMITS.bullets).default([]),
  })
  .strict();

export const projectItemFormSchema = z
  .object({
    name: z.string().max(DOCUMENT_LIMITS.itemField).default(""),
    url: z.string().max(DOCUMENT_LIMITS.url).default(""),
    bullets: z.array(bulletBoxSchema).max(DOCUMENT_LIMITS.bullets).default([]),
  })
  .strict();

export const resumeDocumentFormSchema = z
  .object({
    basics: resumeBasicsFormSchema.default(resumeBasicsFormSchema.parse({})),
    summary: z.string().max(DOCUMENT_LIMITS.summary).default(""),
    experience: z
      .array(experienceItemFormSchema)
      .max(DOCUMENT_LIMITS.experience)
      .default([]),
    education: z
      .array(educationItemFormSchema)
      .max(DOCUMENT_LIMITS.education)
      .default([]),
    skills: z.array(skillBoxSchema).max(DOCUMENT_LIMITS.skills).default([]),
    projects: z
      .array(projectItemFormSchema)
      .max(DOCUMENT_LIMITS.projects)
      .default([]),
  })
  .strict();

export type ResumeDocumentFormValues = z.infer<typeof resumeDocumentFormSchema>;
export type ExperienceItemFormValues = z.infer<typeof experienceItemFormSchema>;
export type EducationItemFormValues = z.infer<typeof educationItemFormSchema>;
export type ProjectItemFormValues = z.infer<typeof projectItemFormSchema>;

/** API content -> form state (on load): box every primitive element. */
export function contentFromWire(
  wire: ResumeDocumentValues
): ResumeDocumentFormValues {
  return {
    basics: {
      name: wire.basics.name,
      email: wire.basics.email,
      phone: wire.basics.phone,
      location: wire.basics.location,
      links: wire.basics.links.map((value) => ({ value })),
    },
    summary: wire.summary,
    experience: wire.experience.map((item) => ({
      title: item.title,
      company: item.company,
      start: item.start,
      end: item.end,
      bullets: item.bullets.map((value) => ({ value })),
    })),
    education: wire.education.map((item) => ({
      school: item.school,
      degree: item.degree,
      start: item.start,
      end: item.end,
      bullets: item.bullets.map((value) => ({ value })),
    })),
    skills: wire.skills.map((value) => ({ value })),
    projects: wire.projects.map((item) => ({
      name: item.name,
      url: item.url,
      bullets: item.bullets.map((value) => ({ value })),
    })),
  };
}

/** Form state -> API content (before PUT): unbox. The INVERSE of
 * contentFromWire; tested to roundtrip losslessly and to parse clean
 * through resumeDocumentSaveSchema (the {value}-leak hazard pin). */
export function contentToWire(
  form: ResumeDocumentFormValues
): ResumeDocumentValues {
  return {
    basics: {
      name: form.basics.name,
      email: form.basics.email,
      phone: form.basics.phone,
      location: form.basics.location,
      links: form.basics.links.map((entry) => entry.value),
    },
    summary: form.summary,
    experience: form.experience.map((item) => ({
      title: item.title,
      company: item.company,
      start: item.start,
      end: item.end,
      bullets: item.bullets.map((entry) => entry.value),
    })),
    education: form.education.map((item) => ({
      school: item.school,
      degree: item.degree,
      start: item.start,
      end: item.end,
      bullets: item.bullets.map((entry) => entry.value),
    })),
    skills: form.skills.map((entry) => entry.value),
    projects: form.projects.map((item) => ({
      name: item.name,
      url: item.url,
      bullets: item.bullets.map((entry) => entry.value),
    })),
  };
}

/** The canonical empty FORM state (P8-3) - derived from the form schema. */
export function emptyResumeDocumentForm(): ResumeDocumentFormValues {
  return resumeDocumentFormSchema.parse({});
}

/** Append payloads for the object field arrays (form-shaped items). */
export function emptyExperienceItemForm(): ExperienceItemFormValues {
  return experienceItemFormSchema.parse({});
}

export function emptyEducationItemForm(): EducationItemFormValues {
  return educationItemFormSchema.parse({});
}

export function emptyProjectItemForm(): ProjectItemFormValues {
  return projectItemFormSchema.parse({});
}
