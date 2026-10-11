"use client";

/**
 * Structured section forms for the resume document editor (P8-6, D12).
 *
 * The editor uses React Hook Form + Zod per the locked stack (D12'), with
 * useFieldArray for EVERY repeatable list; items are appended as complete
 * empty shapes from the schema helpers so partial objects can never enter
 * form state. No drag-reorder (D12 scope discipline).
 *
 * D14-1: form state boxes every field-array element as {value: string}
 * (RHF 7.53 cannot double-append into primitive arrays - evidence in
 * document-schema.ts). Primitive lists append {value: ""} and register
 * through .value; the mappers at the API boundary handle the conversion.
 *
 * RHF 7.53 notes (both evidence-backed, not style choices):
 * - Do NOT pass `control` to useFieldArray here: with control passed,
 *   name typing breaks for this form shape (three independent tsc runs).
 *   Omitting it uses the useFormContext control - the runtime-identical
 *   fallback, proven by this file's own passing tests.
 * - FieldArrayPath cannot express two-level array nesting
 *   (experience.N.bullets), so BulletListEditor casts its hook's name to
 *   the structurally identical "skills" path. TYPE-ONLY: the runtime
 *   path is the real nested path.
 *
 * Caps are hard maxLength attributes: overflow cannot be typed, so per-
 * field error text is rendered only where it can realistically appear;
 * the backend re-validates every save regardless (it is the authority).
 */

import type { Path } from "react-hook-form";
import { useFieldArray, useFormContext } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  DOCUMENT_LIMITS,
  emptyEducationItemForm,
  emptyExperienceItemForm,
  emptyProjectItemForm,
  type ResumeDocumentFormValues,
} from "@/lib/resumes/document-schema";

function SectionHeading({ id, children }: { id: string; children: React.ReactNode }) {
  return (
    <h2 id={id} className="text-base font-semibold text-ink">
      {children}
    </h2>
  );
}

function FieldError({ message }: { message?: string }) {
  if (!message) return null;
  return (
    <p role="alert" className="text-xs text-red-600">
      {message}
    </p>
  );
}

type BulletListName =
  | `experience.${number}.bullets`
  | `education.${number}.bullets`
  | `projects.${number}.bullets`;

function BulletListEditor({
  name,
  addLabel,
  removeLabel,
}: {
  /** Runtime path, e.g. "experience.0.bullets". See the module note on
   * RHF 7.53 typing: the hook below casts to the structurally identical
   * "skills" path for TYPES only. */
  name: BulletListName;
  addLabel: string;
  removeLabel: string;
}) {
  const { register } = useFormContext<ResumeDocumentFormValues>();
  const { fields, append, remove } = useFieldArray({
    name: name as unknown as "skills",
  });
  return (
    <div className="space-y-2">
      {fields.map((field, index) => (
        <div key={field.id} className="flex items-start gap-2">
          <div className="flex-1 space-y-1">
            <Label htmlFor={`${name}-${index}-bullet`} className="sr-only">
              {`${addLabel} ${index + 1}`}
            </Label>
            <textarea
              id={`${name}-${index}-bullet`}
              rows={2}
              maxLength={DOCUMENT_LIMITS.bullet}
              placeholder="Accomplishment with a number or result..."
              className="w-full rounded-neu bg-base px-4 py-3 text-sm text-ink shadow-neu-inset placeholder:text-ink-soft"
              {...register(`${name}.${index}.value` as Path<ResumeDocumentFormValues>)}
            />
          </div>
          <Button
            type="button"
            aria-label={`${removeLabel} ${index + 1}`}
            onClick={() => remove(index)}
          >
            Remove
          </Button>
        </div>
      ))}
      <div>
        <Button type="button" onClick={() => append({ value: "" })}>
          {addLabel}
        </Button>
      </div>
    </div>
  );
}

export function BasicsSection() {
  const {
    register,
    formState: { errors },
  } = useFormContext<ResumeDocumentFormValues>();
  const { fields, append, remove } = useFieldArray({ name: "basics.links" });

  return (
    <section aria-labelledby="basics-heading" className="space-y-4">
      <SectionHeading id="basics-heading">Contact details</SectionHeading>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="basics-name">Name</Label>
          <Input
            id="basics-name"
            type="text"
            maxLength={DOCUMENT_LIMITS.name}
            placeholder="Ada Lovelace"
            {...register("basics.name")}
          />
          <FieldError message={errors.basics?.name?.message} />
        </div>
        {/* type="text" on purpose: resume display content, not an account
            credential - the backend deliberately does not EmailStr this. */}
        <div className="space-y-1.5">
          <Label htmlFor="basics-email">Email</Label>
          <Input
            id="basics-email"
            type="text"
            maxLength={DOCUMENT_LIMITS.email}
            placeholder="ada@example.com"
            {...register("basics.email")}
          />
          <FieldError message={errors.basics?.email?.message} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="basics-phone">Phone</Label>
          <Input
            id="basics-phone"
            type="text"
            maxLength={DOCUMENT_LIMITS.phone}
            placeholder="+1 555 0100"
            {...register("basics.phone")}
          />
          <FieldError message={errors.basics?.phone?.message} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="basics-location">Location</Label>
          <Input
            id="basics-location"
            type="text"
            maxLength={DOCUMENT_LIMITS.location}
            placeholder="London"
            {...register("basics.location")}
          />
          <FieldError message={errors.basics?.location?.message} />
        </div>
      </div>
      <div className="space-y-2">
        {fields.map((field, index) => (
          <div key={field.id} className="flex items-center gap-2">
            <div className="flex-1 space-y-1">
              <Label htmlFor={`basics-link-${index}`} className="sr-only">
                {`Link ${index + 1}`}
              </Label>
              <Input
                id={`basics-link-${index}`}
                type="text"
                maxLength={DOCUMENT_LIMITS.link}
                placeholder="https://github.com/you"
                {...register(`basics.links.${index}.value` as Path<ResumeDocumentFormValues>)}
              />
            </div>
            <Button
              type="button"
              aria-label={`Remove link ${index + 1}`}
              onClick={() => remove(index)}
            >
              Remove
            </Button>
          </div>
        ))}
        <div>
          <Button type="button" onClick={() => append({ value: "" })}>
            Add link
          </Button>
        </div>
      </div>
    </section>
  );
}

export function SummarySection() {
  const {
    register,
    formState: { errors },
  } = useFormContext<ResumeDocumentFormValues>();
  return (
    <section aria-labelledby="summary-heading" className="space-y-4">
      <SectionHeading id="summary-heading">Summary</SectionHeading>
      <div className="space-y-1.5">
        <Label htmlFor="summary">Professional summary</Label>
        <textarea
          id="summary"
          rows={5}
          maxLength={DOCUMENT_LIMITS.summary}
          placeholder="Two or three sentences on who you are and what you bring."
          className="w-full rounded-neu bg-base px-4 py-3 text-sm text-ink shadow-neu-inset placeholder:text-ink-soft"
          {...register("summary")}
        />
        <FieldError message={errors.summary?.message} />
      </div>
    </section>
  );
}

export function ExperienceSection() {
  const { register } = useFormContext<ResumeDocumentFormValues>();
  const { fields, append, remove } = useFieldArray({ name: "experience" });

  return (
    <section aria-labelledby="experience-heading" className="space-y-4">
      <SectionHeading id="experience-heading">Experience</SectionHeading>
      {fields.map((field, index) => (
        <fieldset key={field.id} className="space-y-3 rounded-neu bg-base p-4">
          <legend className="text-sm font-medium text-ink">Role {index + 1}</legend>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor={`experience-${index}-title`}>Title</Label>
              <Input
                id={`experience-${index}-title`}
                type="text"
                maxLength={DOCUMENT_LIMITS.itemField}
                {...register(`experience.${index}.title` as Path<ResumeDocumentFormValues>)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor={`experience-${index}-company`}>Company</Label>
              <Input
                id={`experience-${index}-company`}
                type="text"
                maxLength={DOCUMENT_LIMITS.itemField}
                {...register(`experience.${index}.company` as Path<ResumeDocumentFormValues>)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor={`experience-${index}-start`}>Start</Label>
              <Input
                id={`experience-${index}-start`}
                type="text"
                maxLength={DOCUMENT_LIMITS.date}
                placeholder="Jan 2020"
                {...register(`experience.${index}.start` as Path<ResumeDocumentFormValues>)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor={`experience-${index}-end`}>End</Label>
              <Input
                id={`experience-${index}-end`}
                type="text"
                maxLength={DOCUMENT_LIMITS.date}
                placeholder="Present"
                {...register(`experience.${index}.end` as Path<ResumeDocumentFormValues>)}
              />
            </div>
          </div>
          <BulletListEditor
            name={`experience.${index}.bullets`}
            addLabel="Add bullet"
            removeLabel="Remove bullet"
          />
          <div>
            <Button
              type="button"
              aria-label={`Remove role ${index + 1}`}
              onClick={() => remove(index)}
            >
              Remove role
            </Button>
          </div>
        </fieldset>
      ))}
      <div>
        <Button type="button" onClick={() => append(emptyExperienceItemForm())}>
          Add role
        </Button>
      </div>
    </section>
  );
}

export function EducationSection() {
  const { register } = useFormContext<ResumeDocumentFormValues>();
  const { fields, append, remove } = useFieldArray({ name: "education" });

  return (
    <section aria-labelledby="education-heading" className="space-y-4">
      <SectionHeading id="education-heading">Education</SectionHeading>
      {fields.map((field, index) => (
        <fieldset key={field.id} className="space-y-3 rounded-neu bg-base p-4">
          <legend className="text-sm font-medium text-ink">
            Education {index + 1}
          </legend>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor={`education-${index}-school`}>School</Label>
              <Input
                id={`education-${index}-school`}
                type="text"
                maxLength={DOCUMENT_LIMITS.itemField}
                {...register(`education.${index}.school` as Path<ResumeDocumentFormValues>)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor={`education-${index}-degree`}>Degree</Label>
              <Input
                id={`education-${index}-degree`}
                type="text"
                maxLength={DOCUMENT_LIMITS.itemField}
                {...register(`education.${index}.degree` as Path<ResumeDocumentFormValues>)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor={`education-${index}-start`}>Start</Label>
              <Input
                id={`education-${index}-start`}
                type="text"
                maxLength={DOCUMENT_LIMITS.date}
                {...register(`education.${index}.start` as Path<ResumeDocumentFormValues>)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor={`education-${index}-end`}>End</Label>
              <Input
                id={`education-${index}-end`}
                type="text"
                maxLength={DOCUMENT_LIMITS.date}
                {...register(`education.${index}.end` as Path<ResumeDocumentFormValues>)}
              />
            </div>
          </div>
          <BulletListEditor
            name={`education.${index}.bullets`}
            addLabel="Add bullet"
            removeLabel="Remove bullet"
          />
          <div>
            <Button
              type="button"
              aria-label={`Remove education ${index + 1}`}
              onClick={() => remove(index)}
            >
              Remove education
            </Button>
          </div>
        </fieldset>
      ))}
      <div>
        <Button type="button" onClick={() => append(emptyEducationItemForm())}>
          Add education
        </Button>
      </div>
    </section>
  );
}

export function SkillsSection() {
  const { register } = useFormContext<ResumeDocumentFormValues>();
  const { fields, append, remove } = useFieldArray({ name: "skills" });

  return (
    <section aria-labelledby="skills-heading" className="space-y-4">
      <SectionHeading id="skills-heading">Skills</SectionHeading>
      <div className="space-y-2">
        {fields.map((field, index) => (
          <div key={field.id} className="flex items-center gap-2">
            <div className="flex-1 space-y-1">
              <Label htmlFor={`skill-${index}`} className="sr-only">
                {`Skill ${index + 1}`}
              </Label>
              <Input
                id={`skill-${index}`}
                type="text"
                maxLength={DOCUMENT_LIMITS.skill}
                {...register(`skills.${index}.value` as Path<ResumeDocumentFormValues>)}
              />
            </div>
            <Button
              type="button"
              aria-label={`Remove skill ${index + 1}`}
              onClick={() => remove(index)}
            >
              Remove
            </Button>
          </div>
        ))}
        <div>
          <Button type="button" onClick={() => append({ value: "" })}>
            Add skill
          </Button>
        </div>
      </div>
    </section>
  );
}

export function ProjectsSection() {
  const { register } = useFormContext<ResumeDocumentFormValues>();
  const { fields, append, remove } = useFieldArray({ name: "projects" });

  return (
    <section aria-labelledby="projects-heading" className="space-y-4">
      <SectionHeading id="projects-heading">Projects</SectionHeading>
      {fields.map((field, index) => (
        <fieldset key={field.id} className="space-y-3 rounded-neu bg-base p-4">
          <legend className="text-sm font-medium text-ink">
            Project {index + 1}
          </legend>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor={`projects-${index}-name`}>Project name</Label>
              <Input
                id={`projects-${index}-name`}
                type="text"
                maxLength={DOCUMENT_LIMITS.itemField}
                {...register(`projects.${index}.name` as Path<ResumeDocumentFormValues>)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor={`projects-${index}-url`}>URL</Label>
              <Input
                id={`projects-${index}-url`}
                type="text"
                maxLength={DOCUMENT_LIMITS.url}
                {...register(`projects.${index}.url` as Path<ResumeDocumentFormValues>)}
              />
            </div>
          </div>
          <BulletListEditor
            name={`projects.${index}.bullets`}
            addLabel="Add bullet"
            removeLabel="Remove bullet"
          />
          <div>
            <Button
              type="button"
              aria-label={`Remove project ${index + 1}`}
              onClick={() => remove(index)}
            >
              Remove project
            </Button>
          </div>
        </fieldset>
      ))}
      <div>
        <Button type="button" onClick={() => append(emptyProjectItemForm())}>
          Add project
        </Button>
      </div>
    </section>
  );
}
