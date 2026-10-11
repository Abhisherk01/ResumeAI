import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { FormProvider, useForm } from "react-hook-form";

import {
  BasicsSection,
  ExperienceSection,
  SkillsSection,
  SummarySection,
} from "@/components/resumes/editor/document-form-sections";
import {
  emptyResumeDocument,
  type ResumeDocumentValues,
} from "@/lib/resumes/document-schema";

function Harness({ children }: { children: React.ReactNode }) {
  const form = useForm<ResumeDocumentValues>({
    defaultValues: emptyResumeDocument(),
  });
  return (
    <FormProvider {...form}>
      <form onSubmit={(event) => event.preventDefault()}>{children}</form>
    </FormProvider>
  );
}

describe("document form sections", () => {
  it("renders the basics fields with accessible labels", () => {
    render(
      <Harness>
        <BasicsSection />
      </Harness>
    );
    expect(screen.getByLabelText("Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Phone")).toBeInTheDocument();
    expect(screen.getByLabelText("Location")).toBeInTheDocument();
  });

  it("renders the summary textarea", () => {
    render(
      <Harness>
        <SummarySection />
      </Harness>
    );
    expect(screen.getByLabelText(/professional summary/i)).toBeInTheDocument();
  });

  it("adds an experience item with title and company fields", async () => {
    const user = userEvent.setup();
    render(
      <Harness>
        <ExperienceSection />
      </Harness>
    );
    await user.click(screen.getByRole("button", { name: /add role/i }));
    expect(screen.getByLabelText("Title")).toBeInTheDocument();
    expect(screen.getByLabelText("Company")).toBeInTheDocument();
  });

  it("adds two roles to the same array (multi-append)", async () => {
    const user = userEvent.setup();
    render(
      <Harness>
        <ExperienceSection />
      </Harness>
    );
    await user.click(screen.getByRole("button", { name: /add role/i }));
    expect(screen.getByLabelText("Title")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /add role/i }));
    await waitFor(
      () => expect(screen.getAllByLabelText("Title")).toHaveLength(2),
      { timeout: 5000 }
    );
  });

  it("adds a nested bullet inside an experience item", async () => {
    const user = userEvent.setup();
    render(
      <Harness>
        <ExperienceSection />
      </Harness>
    );
    await user.click(screen.getByRole("button", { name: /add role/i }));
    await user.click(screen.getByRole("button", { name: "Add bullet" }));
    expect(screen.getByLabelText("Add bullet 1")).toBeInTheDocument();
  });

  it("adds and removes skills", async () => {
    const user = userEvent.setup();
    render(
      <Harness>
        <SkillsSection />
      </Harness>
    );
    await user.click(screen.getByRole("button", { name: /add skill/i }));
    expect(await screen.findByLabelText("Skill 1")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /add skill/i }));
    // Generous waits: under heavy machine load (vitest fork workers
    // starting slowly) RHF's state flush can outlive findBy's default
    // 1s. This asserts the real contract - the row appears - without
    // mistaking load for a bug.
    await waitFor(
      () => expect(screen.getAllByLabelText(/Skill /)).toHaveLength(2),
      { timeout: 5000 }
    );

    await user.click(screen.getByRole("button", { name: /remove skill 1/i }));
    // Remaining item re-indexes to Skill 1 - exactly one input remains:
    await waitFor(
      () => expect(screen.getAllByLabelText(/Skill /)).toHaveLength(1),
      { timeout: 5000 }
    );
  });

  it("adds a link in the basics section", async () => {
    const user = userEvent.setup();
    render(
      <Harness>
        <BasicsSection />
      </Harness>
    );
    await user.click(screen.getByRole("button", { name: /add link/i }));
    expect(screen.getByLabelText("Link 1")).toBeInTheDocument();
  });
});
