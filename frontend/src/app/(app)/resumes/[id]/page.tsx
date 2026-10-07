import type { Metadata } from "next";

import { ResumeDetailClient } from "@/components/resumes/resume-detail-client";

export const metadata: Metadata = { title: "Resume - ResumeAI" };

export default function ResumeDetailPage() {
  return <ResumeDetailClient />;
}
