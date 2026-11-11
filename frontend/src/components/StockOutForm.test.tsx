
import { afterEach, describe, expect, it, vi } from "vitest";
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import StockOutForm from "./StockOutForm";
import { stockOut } from "../api/inventory";

vi.mock("../api/inventory", () => ({
  stockOut: vi.fn(),
}));

const mockedStockOut = vi.mocked(stockOut);

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("StockOutForm", () => {
  it("renders the medication name and available quantity", () => {
    render(
      <StockOutForm
        medicationId={6}
        medicationName="Integration Test Medication"
        availableQuantity={105}
      />
    );

    expect(
      screen.getByText("Stock OUT — Integration Test Medication")
    ).toBeInTheDocument();

    expect(
      screen.getByText("Available inventory: 105")
    ).toBeInTheDocument();
  });

  it("rejects zero quantities", async () => {
    const user = userEvent.setup();

    render(
      <StockOutForm
        medicationId={6}
        medicationName="Integration Test Medication"
        availableQuantity={105}
      />
    );

    await user.type(
      screen.getByLabelText("Quantity to remove"),
      "0"
    );

    await user.click(
      screen.getByRole("button", { name: "Remove Stock" })
    );

    expect(mockedStockOut).not.toHaveBeenCalled();
  });

  it("rejects quantities exceeding available inventory", async () => {
    const user = userEvent.setup();

    render(
      <StockOutForm
        medicationId={6}
        medicationName="Integration Test Medication"
        availableQuantity={105}
      />
    );

    await user.type(
      screen.getByLabelText("Quantity to remove"),
      "200"
    );

    await user.click(
      screen.getByRole("button", { name: "Remove Stock" })
    );

    expect(
      await screen.findByRole("alert")
    ).toHaveTextContent(
      "Insufficient inventory. Available quantity: 105"
    );

    expect(mockedStockOut).not.toHaveBeenCalled();
  });

  it("submits a valid quantity and calls onSuccess", async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();

    const transaction = {
      id: 3,
      medication_id: 6,
      action: "OUT" as const,
      quantity: 20,
      timestamp: "2026-11-10T13:00:00",
    };

    mockedStockOut.mockResolvedValue(transaction);

    render(
      <StockOutForm
        medicationId={6}
        medicationName="Integration Test Medication"
        availableQuantity={105}
        onSuccess={onSuccess}
      />
    );

    await user.type(
      screen.getByLabelText("Quantity to remove"),
      "20"
    );

    await user.click(
      screen.getByRole("button", { name: "Remove Stock" })
    );

    expect(mockedStockOut).toHaveBeenCalledWith(6, 20);

    expect(
      await screen.findByRole("status")
    ).toHaveTextContent(
      "Successfully removed 20 units"
    );

    expect(onSuccess).toHaveBeenCalledWith(transaction);
  });

  it("displays API errors when Stock OUT fails", async () => {
    const user = userEvent.setup();

    mockedStockOut.mockRejectedValue(
      new Error("Insufficient inventory")
    );

    render(
      <StockOutForm
        medicationId={6}
        medicationName="Integration Test Medication"
        availableQuantity={105}
      />
    );

    await user.type(
      screen.getByLabelText("Quantity to remove"),
      "20"
    );

    await user.click(
      screen.getByRole("button", { name: "Remove Stock" })
    );

    expect(
      await screen.findByRole("alert")
    ).toHaveTextContent("Insufficient inventory");
  });
});
