
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  render,
  screen,
  fireEvent,
  waitFor,
} from "@testing-library/react";

import EditMedicationForm from "./EditMedicationForm";
import {
  updateMedication,
  type Medication,
} from "../services/medicationApi";

vi.mock("../services/medicationApi", () => ({
  updateMedication: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("EditMedicationForm", () => {
  const testMedication: Medication = {
    id: 1,
    name: "Amoxicillin 500 mg",
    brand: "Generic",
    ndc: "12345678901",
    expiration_date: "2027-12-31",
    lot_number: "TESTLOT001",
    quantity: 75,
  };

  it("loads existing medication information into the form", () => {
    const onMedicationUpdated = vi.fn();
    const onCancel = vi.fn();

    render(
      <EditMedicationForm
        medication={testMedication}
        onMedicationUpdated={onMedicationUpdated}
        onCancel={onCancel}
      />
    );

    expect(
      screen.getByRole("heading", {
        name: "Edit Medication",
      })
    ).toBeTruthy();

    expect(
      (screen.getByLabelText("Medication Name") as HTMLInputElement)
        .value
    ).toBe("Amoxicillin 500 mg");

    expect(
      (screen.getByLabelText("Brand") as HTMLInputElement)
        .value
    ).toBe("Generic");

    expect(
      (screen.getByLabelText("NDC (11 digits)") as HTMLInputElement)
        .value
    ).toBe("12345678901");

    expect(
      (screen.getByLabelText("Expiration Date") as HTMLInputElement)
        .value
    ).toBe("2027-12-31");

    expect(
      (screen.getByLabelText("Lot Number") as HTMLInputElement)
        .value
    ).toBe("TESTLOT001");

    expect(
      (screen.getByLabelText("Quantity") as HTMLInputElement)
        .value
    ).toBe("75");

    expect(
      screen.getByRole("button", { name: "Save Changes" })
    ).toBeTruthy();

    expect(
      screen.getByRole("button", { name: "Cancel" })
    ).toBeTruthy();
  });

it("successfully updates an existing medication", async () => {
  const onMedicationUpdated = vi.fn();
  const onCancel = vi.fn();

  const updatedMedication: Medication = {
    ...testMedication,
    quantity: 100,
  };

  vi.mocked(updateMedication).mockResolvedValueOnce(
    updatedMedication
  );

  render(
    <EditMedicationForm
      medication={testMedication}
      onMedicationUpdated={onMedicationUpdated}
      onCancel={onCancel}
    />
  );

  // Change the existing quantity from 75 to 100.
  fireEvent.change(screen.getByLabelText("Quantity"), {
    target: { value: "100" },
  });

  fireEvent.click(
    screen.getByRole("button", { name: "Save Changes" })
  );

  // Verify that the API receives the correct ID and fields.
  await waitFor(() => {
    expect(updateMedication).toHaveBeenCalledWith(1, {
      name: "Amoxicillin 500 mg",
      brand: "Generic",
      ndc: "12345678901",
      expiration_date: "2027-12-31",
      lot_number: "TESTLOT001",
      quantity: 100,
    });
  });

  // Verify that React receives the updated medication.
  expect(onMedicationUpdated).toHaveBeenCalledWith(
    updatedMedication
  );

  // Successful updates should not trigger cancellation.
  expect(onCancel).not.toHaveBeenCalled();

  // No validation or API error should be displayed.
  expect(screen.queryByRole("alert")).toBeNull();
});

it("cancels editing without saving changes", () => {
  const onMedicationUpdated = vi.fn();
  const onCancel = vi.fn();

  render(
    <EditMedicationForm
      medication={testMedication}
      onMedicationUpdated={onMedicationUpdated}
      onCancel={onCancel}
    />
  );

  // Change the quantity without saving.
  fireEvent.change(screen.getByLabelText("Quantity"), {
    target: { value: "200" },
  });

  // Click Cancel instead of Save Changes.
  fireEvent.click(
    screen.getByRole("button", { name: "Cancel" })
  );

  // Verify that the cancellation callback runs.
  expect(onCancel).toHaveBeenCalledTimes(1);

  // Verify that no update was submitted.
  expect(updateMedication).not.toHaveBeenCalled();

  // Verify that the update callback was not triggered.
  expect(onMedicationUpdated).not.toHaveBeenCalled();
});

it("rejects an invalid NDC without calling the API", async () => {
  const onMedicationUpdated = vi.fn();
  const onCancel = vi.fn();

  render(
    <EditMedicationForm
      medication={testMedication}
      onMedicationUpdated={onMedicationUpdated}
      onCancel={onCancel}
    />
  );

  // Enter an invalid NDC containing only five digits.
  fireEvent.change(
    screen.getByLabelText("NDC (11 digits)"),
    {
      target: { value: "12345" },
    }
  );

  // Attempt to save the medication.
  fireEvent.click(
    screen.getByRole("button", { name: "Save Changes" })
  );

  // The API must not receive an invalid medication.
  expect(updateMedication).not.toHaveBeenCalled();

  // The parent component must not receive an update.
  expect(onMedicationUpdated).not.toHaveBeenCalled();

  // The edit form should remain open.
  expect(onCancel).not.toHaveBeenCalled();
});

it("rejects negative quantities without calling the API", () => {
  const onMedicationUpdated = vi.fn();
  const onCancel = vi.fn();

  render(
    <EditMedicationForm
      medication={testMedication}
      onMedicationUpdated={onMedicationUpdated}
      onCancel={onCancel}
    />
  );

  // Attempt to enter a negative inventory quantity.
  fireEvent.change(screen.getByLabelText("Quantity"), {
    target: { value: "-10" },
  });

  // Attempt to save the medication.
  fireEvent.click(
    screen.getByRole("button", { name: "Save Changes" })
  );

  // Invalid inventory data must not reach the API.
  expect(updateMedication).not.toHaveBeenCalled();

  // No successful update should be reported.
  expect(onMedicationUpdated).not.toHaveBeenCalled();

  // The form should not be canceled.
  expect(onCancel).not.toHaveBeenCalled();
});

it("handles duplicate medication errors without updating", async () => {
  const onMedicationUpdated = vi.fn();
  const onCancel = vi.fn();

  // Simulate the API rejecting a duplicate NDC/lot combination.
  vi.mocked(updateMedication).mockRejectedValueOnce(
    new Error(
      "A medication with this NDC and lot number already exists."
    )
  );

  render(
    <EditMedicationForm
      medication={testMedication}
      onMedicationUpdated={onMedicationUpdated}
      onCancel={onCancel}
    />
  );

  // Attempt to save the medication.
  fireEvent.click(
    screen.getByRole("button", { name: "Save Changes" })
  );

  // Verify the API was called.
  await waitFor(() => {
    expect(updateMedication).toHaveBeenCalledTimes(1);
  });

  // Verify the error is displayed to the user.
  expect(
    await screen.findByText(
      "A medication with this NDC and lot number already exists."
    )
  ).toBeTruthy();

  // An unsuccessful request must not update the UI.
  expect(onMedicationUpdated).not.toHaveBeenCalled();

  // The editing form should remain available.
  expect(onCancel).not.toHaveBeenCalled();
});

});
