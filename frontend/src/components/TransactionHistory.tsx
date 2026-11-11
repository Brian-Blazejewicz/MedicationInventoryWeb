
import { useEffect, useState } from "react";
import { getInventoryTransactions } from "../api/inventory";
import type { InventoryTransaction } from "../types/inventory";

interface TransactionHistoryProps {
  medicationId: number;
  medicationName: string;
}

export default function TransactionHistory({
  medicationId,
  medicationName,
}: TransactionHistoryProps) {
  const [transactions, setTransactions] = useState<
    InventoryTransaction[]
  >([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadTransactions() {
      try {
        const data = await getInventoryTransactions(medicationId);

        if (active) {
          setTransactions(data);
          setError(null);
        }
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load transaction history."
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadTransactions();

    return () => {
      active = false;
    };
  }, [medicationId]);

  function formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);

    if (Number.isNaN(date.getTime())) {
      return timestamp;
    }

    return date.toLocaleString();
  }

  return (
    <section aria-label="Medication transaction history">
      <h3>Transaction History — {medicationName}</h3>

      {loading && <p>Loading transaction history...</p>}

      {error && <p role="alert">{error}</p>}

      {!loading && !error && (
        <>
          <p>Total transactions: {transactions.length}</p>

          {transactions.length === 0 ? (
            <p>No inventory transactions recorded.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Quantity</th>
                  <th>Date / Time</th>
                </tr>
              </thead>

              <tbody>
                {transactions.map((transaction) => (
                  <tr key={transaction.id}>
                    <td>{transaction.action}</td>

                    <td>
                      {transaction.action === "IN" ? "+" : "-"}
                      {transaction.quantity}
                    </td>

                    <td>
                      {formatTimestamp(transaction.timestamp)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </>
      )}
    </section>
  );
}
