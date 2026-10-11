import type { Metadata } from "next";

import { ResumeEditorClient } from "@/components/resumes/editor/resume-editor-client";

export const metadata: Metadata = { title: "Edit Resume - ResumeAI" };

export default function ResumeEditorPage() {
  return <ResumeEditorClient />;
}
