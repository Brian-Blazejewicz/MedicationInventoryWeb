
import type {
  InventoryTransaction,
  InventoryTransactionCreate,
} from "../types/inventory";

const API_BASE_URL = "http://127.0.0.1:8000/api";

async function handleResponse<T>(
  response: Response
): Promise<T> {
  if (!response.ok) {
    let message = `Request failed: ${response.status}`;

    try {
      const errorData: unknown = await response.json();

      if (
        typeof errorData === "object" &&
        errorData !== null &&
        "detail" in errorData
      ) {
        const detail = errorData.detail;

        if (typeof detail === "string") {
          message = detail;
        }
      }
    } catch {
      // Use the default HTTP error message.
    }

    throw new Error(message);
  }

  return (await response.json()) as T;
}

export async function stockIn(
  medicationId: number,
  quantity: number
): Promise<InventoryTransaction> {
  const requestBody: InventoryTransactionCreate = {
    quantity,
  };

  const response = await fetch(
    `${API_BASE_URL}/medications/${medicationId}/stock-in`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    }
  );

  return handleResponse<InventoryTransaction>(response);
}

export async function stockOut(
  medicationId: number,
  quantity: number
): Promise<InventoryTransaction> {
  const requestBody: InventoryTransactionCreate = {
    quantity,
  };

  const response = await fetch(
    `${API_BASE_URL}/medications/${medicationId}/stock-out`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    }
  );

  return handleResponse<InventoryTransaction>(response);
}

export async function getInventoryTransactions(
  medicationId: number
): Promise<InventoryTransaction[]> {
  const response = await fetch(
    `${API_BASE_URL}/medications/${medicationId}/transactions`
  );

  return handleResponse<InventoryTransaction[]>(response);
}
