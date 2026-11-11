
import { useState } from "react";
import { stockIn } from "../api/inventory";
import type { InventoryTransaction } from "../types/inventory";

interface StockInFormProps {
  medicationId: number;
  medicationName: string;
  onSuccess?: (transaction: InventoryTransaction) => void;
}

export default function StockInForm({
  medicationId,
  medicationName,
  onSuccess,
}: StockInFormProps) {
  const [quantity, setQuantity] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const parsedQuantity = Number(quantity);

    if (
      !/^[1-9]\d*$/.test(quantity) ||
      !Number.isSafeInteger(parsedQuantity)
    ) {
      setError("Enter a positive whole number.");
      setSuccess("");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const transaction = await stockIn(
        medicationId,
        parsedQuantity
      );

      setSuccess(
        `Successfully added ${parsedQuantity} units to ${medicationName}.`
      );
      setQuantity("");
      onSuccess?.(transaction);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to add inventory."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h3>Stock IN — {medicationName}</h3>

      <label htmlFor={`stock-in-${medicationId}`}>
        Quantity to add
      </label>

      <input
        id={`stock-in-${medicationId}`}
        type="number"
        min="1"
        step="1"
        value={quantity}
        onChange={(event) => setQuantity(event.target.value)}
        disabled={loading}
        required
      />

      <button type="submit" disabled={loading}>
        {loading ? "Adding Stock..." : "Add Stock"}
      </button>

      {error && <p role="alert">{error}</p>}

      {success && <p role="status">{success}</p>}
    </form>
  );
}
