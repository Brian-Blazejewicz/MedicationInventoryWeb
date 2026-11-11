
export interface Medication {
  id: number;
  name: string;
  brand: string;
  ndc: string;
  expiration_date: string;
  lot_number: string;
  quantity: number;
}

const API_BASE_URL = "http://127.0.0.1:8000";

export async function getMedications(): Promise<Medication[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/medications`
  );

  if (!response.ok) {
    throw new Error(
      `Failed to fetch medications: ${response.status}`
    );
  }

  const medications: Medication[] = await response.json();

  return medications;
}

export type MedicationCreate = Omit<Medication, "id">;

export async function createMedication(
  medication: MedicationCreate
): Promise<Medication> {
  const response = await fetch(
    `${API_BASE_URL}/api/medications`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(medication),
    }
  );

  if (!response.ok) {
    if (response.status === 409) {
      throw new Error(
        "A medication with this NDC and lot number already exists."
      );
    }

    if (response.status === 422) {
      throw new Error(
        "Invalid medication information. Check all fields."
      );
    }

    throw new Error(
      `Failed to create medication: ${response.status}`
    );
  }

  return (await response.json()) as Medication;
}

export async function updateMedication(
  medicationId: number,
  medication: MedicationCreate
): Promise<Medication> {
  const response = await fetch(
    `${API_BASE_URL}/api/medications/${medicationId}`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(medication),
    }
  );

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Medication not found.");
    }

    if (response.status === 409) {
      throw new Error(
        "A medication with this NDC and lot number already exists."
      );
    }

    if (response.status === 422) {
      throw new Error(
        "Invalid medication information. Check all fields."
      );
    }

    throw new Error(
      `Failed to update medication: ${response.status}`
    );
  }

  return (await response.json()) as Medication;
}

export async function deleteMedication(
  medicationId: number
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/medications/${medicationId}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Medication not found.");
    }

    throw new Error(
      `Failed to delete medication: ${response.status}`
    );
  }
}
