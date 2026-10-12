"use client";

/**
 * The resume document editor (P8-6, step 4b-2 integration).
 *
 * Load: GET the document; the backend's DISTINCT document_not_found code
 * (Step 2/D1) is the payoff here - it means "start empty" (P8-3), not an
 * error. Every other failure is a real error surface.
 *
 * Save: one explicit Save -> the upsert PUT (D2); the client never needs
 * to know create-vs-update. Template/accent selection lives in state
 * (D15), initialized from the saved row (or classic/blue on an empty
 * start), edited in memory, and persisted by the next save TOGETHER with
 * the content. A successful save bumps refreshKey so the preview pane
 * (D16) refetches; the pane always shows the LAST SAVED state (D3),
 * never unsaved edits. Form state is the D14-1 boxed shape; the pure
 * mappers convert at the boundary so the backend contract is inviolate.
 */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useForm, FormProvider } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import {
  describeApiError,
  describeUnknownError,
} from "@/components/auth/api-error-message";
import {
  AccentPicker,
  TemplatePicker,
} from "@/components/resumes/editor/document-pickers";
import { DocumentPreviewPane } from "@/components/resumes/editor/document-preview-pane";
import { ExportDocumentButton } from "@/components/resumes/editor/export-document-button";
import {
  BasicsSection,
  EducationSection,
  ExperienceSection,
  ProjectsSection,
  SkillsSection,
  SummarySection,
} from "@/components/resumes/editor/document-form-sections";
import { ApiError } from "@/lib/api/client";
import {
  getResumeDocument,
  saveResumeDocument,
} from "@/lib/api/resume-documents";
import {
  contentFromWire,
  contentToWire,
  emptyResumeDocumentForm,
  resumeDocumentFormSchema,
  type ResumeDocumentFormValues,
  type ResumeAccent,
  type ResumeTemplateId,
} from "@/lib/resumes/document-schema";
import { Button } from "@/components/ui/button";
import { FormError } from "@/components/ui/form-error";

export function ResumeEditorClient() {
  const params = useParams<{ id: string }>();
  const resumeId = params.id;

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [emptyStart, setEmptyStart] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [savedNotice, setSavedNotice] = useState(false);
  // D15: presentation selection is state - initialized from the saved row
  // (or classic/blue on an empty start), edited in memory, persisted by
  // the next save together with the content (D2's upsert semantics).
  const [templateId, setTemplateId] = useState<ResumeTemplateId>("classic");
  const [accent, setAccent] = useState<ResumeAccent>("blue");
  // D16: bumped after every successful save so the preview refetches.
  const [refreshKey, setRefreshKey] = useState(0);

  const form = useForm<ResumeDocumentFormValues>({
    resolver: zodResolver(resumeDocumentFormSchema),
    defaultValues: emptyResumeDocumentForm(),
  });

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const data = await getResumeDocument(resumeId);
      form.reset(contentFromWire(data.content));
      setTemplateId(data.template_id);
      setAccent(data.accent);
      setEmptyStart(false);
    } catch (error) {
      if (error instanceof ApiError && error.code === "document_not_found") {
        // D1 payoff: this code exists so the editor can start empty
        // instead of treating a first visit as a failure (P8-3).
        form.reset(emptyResumeDocumentForm());
        setTemplateId("classic");
        setAccent("blue");
        setEmptyStart(true);
      } else {
        setLoadError(
          error instanceof ApiError
            ? describeApiError(error)
            : describeUnknownError()
        );
      }
    } finally {
      setLoading(false);
    }
  }, [resumeId, form]);

  useEffect(() => {
    void load();
  }, [load]);

  const onSubmit = form.handleSubmit(async (values) => {
    setSaveError(null);
    setSavedNotice(false);
    setSaving(true);
    try {
      const saved = await saveResumeDocument(resumeId, {
        template_id: templateId,
        accent: accent,
        content: contentToWire(values),
      });
      setTemplateId(saved.template_id);
      setAccent(saved.accent);
      setRefreshKey((key) => key + 1);
      setEmptyStart(false);
      setSavedNotice(true);
    } catch (error) {
      setSaveError(
        error instanceof ApiError
          ? describeApiError(error)
          : describeUnknownError()
      );
    } finally {
      setSaving(false);
    }
  });

  if (loading) {
    return (
      <p className="text-sm text-ink-soft" role="status">
        Loading document...
      </p>
    );
  }

  if (loadError) {
    return (
      <div className="space-y-3">
        <FormError>{loadError ?? undefined}</FormError>
        <Link
          href={`/resumes/${resumeId}`}
          className="text-sm font-medium text-accent hover:underline"
        >
          Back to resume
        </Link>
      </div>
    );
  }

  return (
    <FormProvider {...form}>
      <form onSubmit={onSubmit} noValidate className="space-y-8">
        <div className="space-y-1">
          <h1 className="text-xl font-semibold text-ink">Edit document</h1>
          <p className="text-sm text-ink-soft">
            Structure your resume for the four templates. Nothing is stored
            until you save.
          </p>
        </div>

        {emptyStart && (
          <p role="note" className="text-sm text-ink-soft">
            No saved document yet - start filling the sections below. The
            original upload and its analysis history are never modified.
          </p>
        )}

        <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_400px]">
          <div className="space-y-8">
            <div className="grid gap-6 sm:grid-cols-2">
              <TemplatePicker value={templateId} onChange={setTemplateId} />
              <AccentPicker value={accent} onChange={setAccent} />
            </div>

            <BasicsSection />
            <SummarySection />
            <ExperienceSection />
            <EducationSection />
            <SkillsSection />
            <ProjectsSection />

            <FormError>{saveError ?? undefined}</FormError>
            {savedNotice && (
              <p role="status" className="text-sm text-ink">
                Document saved.
              </p>
            )}

            <div className="flex items-center gap-3">
              <Button type="submit" loading={saving}>
                Save document
              </Button>
              <Link
                href={`/resumes/${resumeId}`}
                className="text-sm font-medium text-accent hover:underline"
              >
                Back to resume
              </Link>
            </div>
          </div>

          <div className="space-y-6">
            <DocumentPreviewPane resumeId={resumeId} refreshKey={refreshKey} />
            <ExportDocumentButton resumeId={resumeId} />
          </div>
        </div>
      </form>
    </FormProvider>
  );
}
