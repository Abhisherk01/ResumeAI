import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ToastProvider, useToast } from "./toast";

function Trigger() {
  const { toast } = useToast();
  return (
    <button
      type="button"
      onClick={() =>
        toast({ title: "Resume saved", description: "All changes stored.", variant: "success" })
      }
    >
      Save
    </button>
  );
}

describe("ToastProvider", () => {
  it("shows a toast with title, description, and a dismiss control", async () => {
    render(
      <ToastProvider>
        <Trigger />
      </ToastProvider>
    );
    await userEvent.setup().click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Resume saved")).toBeInTheDocument();
    expect(screen.getByText("All changes stored.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Dismiss notification" })).toBeInTheDocument();
  });
});
