
import { useState } from "react";
import type { FormEvent } from "react";
import { stockOut } from "../api/inventory";
import type { InventoryTransaction } from "../types/inventory";

interface StockOutFormProps {
  medicationId: number;
  medicationName: string;
  availableQuantity: number;
  onSuccess?: (transaction: InventoryTransaction) => void;
}

export default function StockOutForm({
  medicationId,
  medicationName,
  availableQuantity,
  onSuccess,
}: StockOutFormProps) {
  const [quantity, setQuantity] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
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

    if (parsedQuantity > availableQuantity) {
      setError(
        `Insufficient inventory. Available quantity: ${availableQuantity}`
      );
      setSuccess("");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const transaction = await stockOut(
        medicationId,
        parsedQuantity
      );

      setSuccess(
        `Successfully removed ${parsedQuantity} units from ${medicationName}.`
      );
      setQuantity("");
      onSuccess?.(transaction);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to remove inventory."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h3>Stock OUT — {medicationName}</h3>

      <p>Available inventory: {availableQuantity}</p>

      <label htmlFor={`stock-out-${medicationId}`}>
        Quantity to remove
      </label>

      <input
        id={`stock-out-${medicationId}`}
        type="number"
        min="1"
        step="1"
        value={quantity}
        onChange={(event) => setQuantity(event.target.value)}
        disabled={loading}
        required
      />

      <button type="submit" disabled={loading}>
        {loading ? "Removing Stock..." : "Remove Stock"}
      </button>

      {error && <p role="alert">{error}</p>}

      {success && <p role="status">{success}</p>}
    </form>
  );
}
