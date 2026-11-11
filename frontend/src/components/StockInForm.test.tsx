
import { afterEach, describe, expect, it, vi } from "vitest";
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import StockInForm from "./StockInForm";
import { stockIn } from "../api/inventory";

vi.mock("../api/inventory", () => ({
  stockIn: vi.fn(),
}));

const mockedStockIn = vi.mocked(stockIn);

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("StockInForm", () => {
  it("renders the correct medication name", () => {
    render(
      <StockInForm
        medicationId={6}
        medicationName="Integration Test Medication"
      />
    );

    expect(
      screen.getByText("Stock IN — Integration Test Medication")
    ).toBeInTheDocument();
  });

  it("rejects zero quantities", async () => {
    const user = userEvent.setup();

    render(
      <StockInForm
        medicationId={6}
        medicationName="Integration Test Medication"
      />
    );

    const input = screen.getByLabelText("Quantity to add");

    await user.type(input, "0");

    await user.click(
      screen.getByRole("button", { name: "Add Stock" })
    );

    expect(mockedStockIn).not.toHaveBeenCalled();
  });

  it("submits a valid quantity and calls onSuccess", async () => {
    const user = userEvent.setup();
    const onSuccess = vi.fn();

    const transaction = {
      id: 1,
      medication_id: 6,
      action: "IN" as const,
      quantity: 25,
      timestamp: "2026-11-10T12:00:00",
    };

    mockedStockIn.mockResolvedValue(transaction);

    render(
      <StockInForm
        medicationId={6}
        medicationName="Integration Test Medication"
        onSuccess={onSuccess}
      />
    );

    await user.type(
      screen.getByLabelText("Quantity to add"),
      "25"
    );

    await user.click(
      screen.getByRole("button", { name: "Add Stock" })
    );

    expect(mockedStockIn).toHaveBeenCalledWith(6, 25);

    expect(
      await screen.findByRole("status")
    ).toHaveTextContent(
      "Successfully added 25 units"
    );

    expect(onSuccess).toHaveBeenCalledWith(transaction);
  });

  it("displays an API error when Stock IN fails", async () => {
    const user = userEvent.setup();

    mockedStockIn.mockRejectedValue(
      new Error("Database connection failed")
    );

    render(
      <StockInForm
        medicationId={6}
        medicationName="Integration Test Medication"
      />
    );

    await user.type(
      screen.getByLabelText("Quantity to add"),
      "25"
    );

    await user.click(
      screen.getByRole("button", { name: "Add Stock" })
    );

    expect(
      await screen.findByRole("alert")
    ).toHaveTextContent("Database connection failed");
  });
});
