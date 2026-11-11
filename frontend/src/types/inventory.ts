
export type InventoryAction = "IN" | "OUT";

export interface InventoryTransaction {
  id: number;
  medication_id: number;
  action: InventoryAction;
  quantity: number;
  timestamp: string;
}

export interface InventoryTransactionCreate {
  quantity: number;
}
