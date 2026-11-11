
import { useState, type FormEvent } from "react";
import {
  updateMedication,
  type Medication,
  type MedicationCreate,
} from "../services/medicationApi";

interface EditMedicationFormProps {
  medication: Medication;
  onMedicationUpdated: (medication: Medication) => void;
  onCancel: () => void;
}

function EditMedicationForm({
  medication,
  onMedicationUpdated,
  onCancel,
}: EditMedicationFormProps) {
  const [form, setForm] = useState<MedicationCreate>({
    name: medication.name,
    brand: medication.brand,
    ndc: medication.ndc,
    expiration_date: medication.expiration_date,
    lot_number: medication.lot_number,
    quantity: medication.quantity,
  });

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function updateField<K extends keyof MedicationCreate>(
    field: K,
    value: MedicationCreate[K]
  ) {
    setForm((previous) => ({
      ...previous,
      [field]: value,
    }));

    setError(null);
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!form.name.trim() || !form.brand.trim() ||
        !form.lot_number.trim()) {
      setError("All text fields are required.");
      return;
    }

    if (!/^\d{11}$/.test(form.ndc)) {
      setError("NDC must contain exactly 11 digits.");
      return;
    }

    if (
      !Number.isInteger(form.quantity) ||
      form.quantity < 0
    ) {
      setError("Quantity must be a non-negative whole number.");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const updatedMedication = await updateMedication(
        medication.id,
        form
      );

      onMedicationUpdated(updatedMedication);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to update medication."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section>
      <h2>Edit Medication</h2>

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="edit-name">Medication Name</label>
          <input
            id="edit-name"
            type="text"
            value={form.name}
            maxLength={200}
            required
            onChange={(event) =>
              updateField("name", event.target.value)
            }
          />
        </div>

        <div>
          <label htmlFor="edit-brand">Brand</label>
          <input
            id="edit-brand"
            type="text"
            value={form.brand}
            maxLength={200}
            required
            onChange={(event) =>
              updateField("brand", event.target.value)
            }
          />
        </div>

        <div>
          <label htmlFor="edit-ndc">NDC (11 digits)</label>
          <input
            id="edit-ndc"
            type="text"
            inputMode="numeric"
            pattern="[0-9]{11}"
            maxLength={11}
            value={form.ndc}
            required
            onChange={(event) =>
              updateField("ndc", event.target.value)
            }
          />
        </div>

        <div>
          <label htmlFor="edit-expiration">
            Expiration Date
          </label>
          <input
            id="edit-expiration"
            type="date"
            value={form.expiration_date}
            required
            onChange={(event) =>
              updateField(
                "expiration_date",
                event.target.value
              )
            }
          />
        </div>

        <div>
          <label htmlFor="edit-lot">Lot Number</label>
          <input
            id="edit-lot"
            type="text"
            value={form.lot_number}
            maxLength={100}
            required
            onChange={(event) =>
              updateField("lot_number", event.target.value)
            }
          />
        </div>

        <div>
          <label htmlFor="edit-quantity">Quantity</label>
          <input
            id="edit-quantity"
            type="number"
            min={0}
            step={1}
            value={form.quantity}
            required
            onChange={(event) =>
              updateField(
                "quantity",
                Number(event.target.value)
              )
            }
          />
        </div>

        {error && <p role="alert">{error}</p>}

        <button type="submit" disabled={submitting}>
          {submitting ? "Saving..." : "Save Changes"}
        </button>

        <button
          type="button"
          onClick={onCancel}
          disabled={submitting}
        >
          Cancel
        </button>
      </form>
    </section>
  );
}

export default EditMedicationForm;
