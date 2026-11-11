
import { useState, type FormEvent } from "react";
import {
  createMedication,
  type Medication,
  type MedicationCreate,
} from "../services/medicationApi";

interface MedicationFormProps {
  onMedicationCreated: (medication: Medication) => void;
}

const initialForm: MedicationCreate = {
  name: "",
  brand: "",
  ndc: "",
  expiration_date: "",
  lot_number: "",
  quantity: 0,
};

function MedicationForm({
  onMedicationCreated,
}: MedicationFormProps) {
  const [form, setForm] =
    useState<MedicationCreate>({ ...initialForm });

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
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
    setSuccess(false);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!/^\d{11}$/.test(form.ndc)) {
      setError("NDC must contain exactly 11 digits.");
      return;
    }

    if (!Number.isInteger(form.quantity) || form.quantity < 0) {
      setError("Quantity must be a non-negative whole number.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setSuccess(false);

    try {
      const medication = await createMedication(form);

      onMedicationCreated(medication);
      setForm({ ...initialForm });
      setSuccess(true);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to add medication."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section>
      <h2>Add Medication</h2>

      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="med-name">Medication Name</label>
          <input
            id="med-name"
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
          <label htmlFor="med-brand">Brand</label>
          <input
            id="med-brand"
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
          <label htmlFor="med-ndc">NDC (11 digits)</label>
          <input
            id="med-ndc"
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
          <label htmlFor="med-expiration">Expiration Date</label>
          <input
            id="med-expiration"
            type="date"
            value={form.expiration_date}
            required
            onChange={(event) =>
              updateField("expiration_date", event.target.value)
            }
          />
        </div>

        <div>
          <label htmlFor="med-lot">Lot Number</label>
          <input
            id="med-lot"
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
          <label htmlFor="med-quantity">Quantity</label>
          <input
            id="med-quantity"
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

        {success && (
          <p role="status">Medication added successfully!</p>
        )}

        <button type="submit" disabled={submitting}>
          {submitting ? "Adding..." : "Add Medication"}
        </button>
      </form>
    </section>
  );
}

export default MedicationForm;
