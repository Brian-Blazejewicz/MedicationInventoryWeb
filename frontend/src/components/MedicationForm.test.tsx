
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  render,
  screen,
  fireEvent,
  cleanup,
  waitFor,
} from "@testing-library/react";
import MedicationForm from "./MedicationForm";
import { createMedication } from "../services/medicationApi";
import type { Medication } from "../services/medicationApi";

vi.mock("../services/medicationApi", () => ({
  createMedication: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("MedicationForm", () => {
  it("renders all required medication fields", () => {
    const onMedicationCreated = vi.fn();

    render(
      <MedicationForm
        onMedicationCreated={onMedicationCreated}
      />
    );

    expect(
      screen.getByRole("heading", { name: "Add Medication" })
    ).toBeTruthy();

    expect(
      screen.getByLabelText("Medication Name")
    ).toBeTruthy();

    expect(
      screen.getByLabelText("Brand")
    ).toBeTruthy();

    expect(
      screen.getByLabelText("NDC (11 digits)")
    ).toBeTruthy();

    expect(
      screen.getByLabelText("Expiration Date")
    ).toBeTruthy();

    expect(
      screen.getByLabelText("Lot Number")
    ).toBeTruthy();

    expect(
      screen.getByLabelText("Quantity")
    ).toBeTruthy();

    expect(
      screen.getByRole("button", { name: "Add Medication" })
    ).toBeTruthy();
  });

it("rejects an NDC that does not contain 11 digits", () => {
  const onMedicationCreated = vi.fn();

  render(
    <MedicationForm
      onMedicationCreated={onMedicationCreated}
    />
  );

  // Enter valid values for the other required fields.
  fireEvent.change(screen.getByLabelText("Medication Name"), {
    target: { value: "Test Medication" },
  });

  fireEvent.change(screen.getByLabelText("Brand"), {
    target: { value: "Test Brand" },
  });

  fireEvent.change(screen.getByLabelText("NDC (11 digits)"), {
    target: { value: "12345" },
  });

  fireEvent.change(screen.getByLabelText("Expiration Date"), {
    target: { value: "2027-12-31" },
  });

  fireEvent.change(screen.getByLabelText("Lot Number"), {
    target: { value: "TESTLOT001" },
  });

  fireEvent.change(screen.getByLabelText("Quantity"), {
    target: { value: "50" },
  });

  // Disable native browser validation so we can
  // test our React validation logic directly.
  const form = screen
    .getByRole("button", { name: "Add Medication" })
    .closest("form");

  expect(form).not.toBeNull();

  fireEvent.submit(form!);

  expect(
    screen.getByRole("alert").textContent
  ).toContain("NDC must contain exactly 11 digits.");

  expect(onMedicationCreated).not.toHaveBeenCalled();
});

it("rejects negative medication quantities", () => {
  const onMedicationCreated = vi.fn();

  render(
    <MedicationForm
      onMedicationCreated={onMedicationCreated}
    />
  );

  // Enter valid medication information.
  fireEvent.change(screen.getByLabelText("Medication Name"), {
    target: { value: "Test Medication" },
  });

  fireEvent.change(screen.getByLabelText("Brand"), {
    target: { value: "Test Brand" },
  });

  fireEvent.change(screen.getByLabelText("NDC (11 digits)"), {
    target: { value: "12345678901" },
  });

  fireEvent.change(screen.getByLabelText("Expiration Date"), {
    target: { value: "2027-12-31" },
  });

  fireEvent.change(screen.getByLabelText("Lot Number"), {
    target: { value: "TESTLOT001" },
  });

  // Enter an invalid negative quantity.
  fireEvent.change(screen.getByLabelText("Quantity"), {
    target: { value: "-5" },
  });

  // Submit directly to test React validation.
  const form = screen
    .getByRole("button", { name: "Add Medication" })
    .closest("form");

  expect(form).not.toBeNull();

  fireEvent.submit(form!);

  expect(screen.getByRole("alert").textContent).toContain(
    "Quantity must be a non-negative whole number."
  );

  expect(onMedicationCreated).not.toHaveBeenCalled();
});

it("successfully creates a medication", async () => {
  const onMedicationCreated = vi.fn();

  const createdMedication: Medication = {
    id: 101,
    name: "Test Medication",
    brand: "Test Brand",
    ndc: "12345678901",
    expiration_date: "2027-12-31",
    lot_number: "TESTLOT001",
    quantity: 50,
  };

  vi.mocked(createMedication).mockResolvedValueOnce(
    createdMedication
  );

  render(
    <MedicationForm
      onMedicationCreated={onMedicationCreated}
    />
  );

  fireEvent.change(screen.getByLabelText("Medication Name"), {
    target: { value: "Test Medication" },
  });

  fireEvent.change(screen.getByLabelText("Brand"), {
    target: { value: "Test Brand" },
  });

  fireEvent.change(screen.getByLabelText("NDC (11 digits)"), {
    target: { value: "12345678901" },
  });

  fireEvent.change(screen.getByLabelText("Expiration Date"), {
    target: { value: "2027-12-31" },
  });

  fireEvent.change(screen.getByLabelText("Lot Number"), {
    target: { value: "TESTLOT001" },
  });

  fireEvent.change(screen.getByLabelText("Quantity"), {
    target: { value: "50" },
  });

  fireEvent.click(
    screen.getByRole("button", { name: "Add Medication" })
  );

  await waitFor(() => {
    expect(createMedication).toHaveBeenCalledWith({
      name: "Test Medication",
      brand: "Test Brand",
      ndc: "12345678901",
      expiration_date: "2027-12-31",
      lot_number: "TESTLOT001",
      quantity: 50,
    });
  });

  expect(onMedicationCreated).toHaveBeenCalledWith(
    createdMedication
  );

  expect(
    screen.getByRole("status").textContent
  ).toContain("Medication added successfully!");

  expect(
    (screen.getByLabelText("Medication Name") as HTMLInputElement)
      .value
  ).toBe("");
});

it("displays an error when a duplicate medication is submitted", async () => {
  const onMedicationCreated = vi.fn();

  // Simulate the error returned by the API service
  // when FastAPI responds with HTTP 409.
  vi.mocked(createMedication).mockRejectedValueOnce(
    new Error(
      "A medication with this NDC and lot number already exists."
    )
  );

  render(
    <MedicationForm
      onMedicationCreated={onMedicationCreated}
    />
  );

  fireEvent.change(screen.getByLabelText("Medication Name"), {
    target: { value: "Test Medication" },
  });

  fireEvent.change(screen.getByLabelText("Brand"), {
    target: { value: "Test Brand" },
  });

  fireEvent.change(screen.getByLabelText("NDC (11 digits)"), {
    target: { value: "12345678901" },
  });

  fireEvent.change(screen.getByLabelText("Expiration Date"), {
    target: { value: "2027-12-31" },
  });

  fireEvent.change(screen.getByLabelText("Lot Number"), {
    target: { value: "TESTLOT001" },
  });

  fireEvent.change(screen.getByLabelText("Quantity"), {
    target: { value: "50" },
  });

  fireEvent.click(
    screen.getByRole("button", { name: "Add Medication" })
  );

  // Wait for the asynchronous API error to appear.
  const errorMessage = await screen.findByRole("alert");

  expect(errorMessage.textContent).toContain(
    "A medication with this NDC and lot number already exists."
  );

  // A failed request must not add a medication.
  expect(onMedicationCreated).not.toHaveBeenCalled();

  // Verify the API function received the submitted data.
  expect(createMedication).toHaveBeenCalledWith({
    name: "Test Medication",
    brand: "Test Brand",
    ndc: "12345678901",
    expiration_date: "2027-12-31",
    lot_number: "TESTLOT001",
    quantity: 50,
  });

  // Preserve form values so the user can correct them.
  expect(
    (screen.getByLabelText("Medication Name") as HTMLInputElement)
      .value
  ).toBe("Test Medication");

  expect(
    (screen.getByLabelText("Lot Number") as HTMLInputElement)
      .value
  ).toBe("TESTLOT001");

  // The user should be able to try again.
  expect(
    (screen.getByRole("button", {
      name: "Add Medication",
    }) as HTMLButtonElement).disabled
  ).toBe(false);
});

});
