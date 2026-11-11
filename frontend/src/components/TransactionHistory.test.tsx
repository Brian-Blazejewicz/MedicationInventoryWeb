
import { afterEach, describe, expect, it, vi } from "vitest";
import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import TransactionHistory from "./TransactionHistory";
import { getInventoryTransactions } from "../api/inventory";

vi.mock("../api/inventory", () => ({
  getInventoryTransactions: vi.fn(),
}));

const mockedGetTransactions = vi.mocked(getInventoryTransactions);

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("TransactionHistory", () => {
  it("displays the correct medication name", async () => {
    mockedGetTransactions.mockResolvedValue([]);

    render(
      <TransactionHistory
        medicationId={6}
        medicationName="Integration Test Medication"
      />
    );

    expect(
      screen.getByText(
        "Transaction History — Integration Test Medication"
      )
    ).toBeInTheDocument();

    expect(
      await screen.findByText("No inventory transactions recorded.")
    ).toBeInTheDocument();
  });

  it("requests transactions for the correct medication", async () => {
    mockedGetTransactions.mockResolvedValue([]);

    render(
      <TransactionHistory
        medicationId={6}
        medicationName="Integration Test Medication"
      />
    );

    expect(
      await screen.findByText("Total transactions: 0")
    ).toBeInTheDocument();

    expect(mockedGetTransactions).toHaveBeenCalledWith(6);
    expect(mockedGetTransactions).toHaveBeenCalledTimes(1);
  });

  it("displays Stock IN and Stock OUT transactions", async () => {
    mockedGetTransactions.mockResolvedValue([
      {
        id: 2,
        medication_id: 6,
        action: "OUT",
        quantity: 20,
        timestamp: "2026-11-10T13:00:00",
      },
      {
        id: 1,
        medication_id: 6,
        action: "IN",
        quantity: 25,
        timestamp: "2026-11-10T12:00:00",
      },
    ]);

    render(
      <TransactionHistory
        medicationId={6}
        medicationName="Integration Test Medication"
      />
    );

    expect(
      await screen.findByText("Total transactions: 2")
    ).toBeInTheDocument();

    expect(screen.getByText("+25")).toBeInTheDocument();
    expect(screen.getByText("-20")).toBeInTheDocument();

    expect(screen.getByText("IN")).toBeInTheDocument();
    expect(screen.getByText("OUT")).toBeInTheDocument();
  });

  it("handles an empty transaction history", async () => {
    mockedGetTransactions.mockResolvedValue([]);

    render(
      <TransactionHistory
        medicationId={6}
        medicationName="Integration Test Medication"
      />
    );

    expect(
      await screen.findByText("No inventory transactions recorded.")
    ).toBeInTheDocument();

    expect(
      screen.getByText("Total transactions: 0")
    ).toBeInTheDocument();
  });

  it("displays an error when the API request fails", async () => {
    mockedGetTransactions.mockRejectedValue(
      new Error("Unable to connect to server")
    );

    render(
      <TransactionHistory
        medicationId={6}
        medicationName="Integration Test Medication"
      />
    );

    expect(
      await screen.findByRole("alert")
    ).toHaveTextContent("Unable to connect to server");

    expect(
      screen.queryByText("Total transactions: 0")
    ).not.toBeInTheDocument();
  });

  it("displays the loading state while waiting for the API", async () => {
    mockedGetTransactions.mockImplementation(
      () => new Promise(() => {})
    );

    render(
      <TransactionHistory
        medicationId={6}
        medicationName="Integration Test Medication"
      />
    );

    expect(
      screen.getByText("Loading transaction history...")
    ).toBeInTheDocument();
  });
});
