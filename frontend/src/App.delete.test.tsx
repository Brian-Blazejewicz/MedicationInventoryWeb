
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";

import App from "./App";
import {
  getMedications,
  deleteMedication,
  type Medication,
} from "./services/medicationApi";

// Mock API functions to avoid changing PostgreSQL.
vi.mock("./services/medicationApi", () => ({
  getMedications: vi.fn(),
  createMedication: vi.fn(),
  updateMedication: vi.fn(),
  deleteMedication: vi.fn(),
}));

const testMedication: Medication = {
  id: 1,
  name: "Delete Test Medication",
  brand: "Test Brand",
  ndc: "99999999992",
  expiration_date: "2027-12-31",
  lot_number: "DELETE001",
  quantity: 10,
};

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("Delete Medication", () => {
  it("opens confirmation for the selected medication", async () => {
    // Simulate loading one medication from FastAPI.
    vi.mocked(getMedications).mockResolvedValueOnce([
      testMedication,
    ]);

    render(<App />);

    // Wait for the medication to load.
    expect(
      await screen.findByText("Delete Test Medication")
    ).toBeTruthy();

    // Click the Delete button for this medication.
    fireEvent.click(
      screen.getByRole("button", { name: "Delete" })
    );

    // Verify the confirmation dialog appears.
    expect(
      screen.getByRole("dialog", {
        name: "Confirm Medication Deletion",
      })
    ).toBeTruthy();

    // Verify the correct medication details are displayed.
    const dialog = screen.getByRole("dialog");

    expect(dialog.textContent).toContain(
      "Delete Test Medication"
    );

    expect(dialog.textContent).toContain(
      "99999999992"
    );

    expect(dialog.textContent).toContain(
      "DELETE001"
    );

    // Opening the dialog must not delete anything.
    expect(deleteMedication).not.toHaveBeenCalled();
  });

it("cancels deletion without removing the medication", async () => {
  // Simulate loading one medication from FastAPI.
  vi.mocked(getMedications).mockResolvedValueOnce([
    testMedication,
  ]);

  render(<App />);

  // Wait for the medication to load.
  expect(
    await screen.findByText("Delete Test Medication")
  ).toBeTruthy();

  // Open the deletion confirmation.
  fireEvent.click(
    screen.getByRole("button", { name: "Delete" })
  );

  // Verify the dialog is open.
  expect(screen.getByRole("dialog")).toBeTruthy();

  // Cancel the deletion.
  fireEvent.click(
    screen.getByRole("button", { name: "Cancel" })
  );

  // Verify the confirmation dialog closes.
  expect(screen.queryByRole("dialog")).toBeNull();

  // Verify the medication remains in the table.
  expect(
    screen.getByText("Delete Test Medication")
  ).toBeTruthy();

  // Verify no DELETE request was sent.
  expect(deleteMedication).not.toHaveBeenCalled();
});

it("successfully deletes a medication and updates the table", async () => {
  // Simulate loading a medication from FastAPI.
  vi.mocked(getMedications).mockResolvedValueOnce([
    testMedication,
  ]);

  // Simulate a successful DELETE request.
  vi.mocked(deleteMedication).mockResolvedValueOnce(
    undefined
  );

  render(<App />);

  // Wait until the medication appears in the table.
  expect(
    await screen.findByText("Delete Test Medication")
  ).toBeTruthy();

  // Open the confirmation dialog.
  fireEvent.click(
    screen.getByRole("button", { name: "Delete" })
  );

  expect(screen.getByRole("dialog")).toBeTruthy();

  // Confirm deletion.
  fireEvent.click(
    screen.getByRole("button", { name: "Confirm Delete" })
  );

  // Verify the correct medication ID was sent to the API.
  await waitFor(() => {
    expect(deleteMedication).toHaveBeenCalledWith(1);
  });

  // Verify React removes the medication after success.
  await waitFor(() => {
    expect(
      screen.queryByText("Delete Test Medication")
    ).toBeNull();
  });

  // The confirmation dialog should close.
  expect(screen.queryByRole("dialog")).toBeNull();

  // The table should now be empty.
  expect(screen.getByText("No medications found.")).toBeTruthy();

  // The displayed medication count should update.
  expect(screen.getByText("Total medications: 0")).toBeTruthy();
});

it("keeps the medication visible when deletion fails", async () => {
  // Simulate loading a medication from FastAPI.
  vi.mocked(getMedications).mockResolvedValueOnce([
    testMedication,
  ]);

  // Simulate a failed DELETE request.
  vi.mocked(deleteMedication).mockRejectedValueOnce(
    new Error("Medication not found.")
  );

  render(<App />);

  // Wait for the medication to load.
  expect(
    await screen.findByText("Delete Test Medication")
  ).toBeTruthy();

  // Open the deletion confirmation dialog.
  fireEvent.click(
    screen.getByRole("button", { name: "Delete" })
  );

  // Attempt to delete the medication.
  fireEvent.click(
    screen.getByRole("button", { name: "Confirm Delete" })
  );

  // Verify the correct medication ID was submitted.
  await waitFor(() => {
    expect(deleteMedication).toHaveBeenCalledWith(1);
  });

  // Verify the API error appears in the dialog.
  expect(
    await screen.findByRole("alert")
  ).toHaveProperty(
    "textContent",
    "Medication not found."
  );

  // The medication must remain in the table.
  
  // Verify the medication remains in the inventory table.
  const medicationRows = screen.getAllByRole("row");

  const medicationRow = medicationRows.find((row) =>
    row.textContent?.includes("Delete Test Medication")
  );

  expect(medicationRow).toBeDefined();


  // The confirmation dialog should remain open.
  expect(screen.getByRole("dialog")).toBeTruthy();

  // The inventory count must remain unchanged.
  expect(
    screen.getByText("Total medications: 1")
  ).toBeTruthy();

  // Cancel should still close the dialog.
  fireEvent.click(
    screen.getByRole("button", { name: "Cancel" })
  );

  expect(screen.queryByRole("dialog")).toBeNull();
});

});
