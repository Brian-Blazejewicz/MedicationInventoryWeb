
import { useEffect, useState } from "react";
import {
  getMedications,
  deleteMedication,
  type Medication,
} from "./services/medicationApi";
import "./App.css";
import MedicationForm from "./components/MedicationForm";
import EditMedicationForm from "./components/EditMedicationForm";
import StockInForm from "./components/StockInForm";
import StockOutForm from "./components/StockOutForm";
import TransactionHistory from "./components/TransactionHistory";

type SortOption = "name" | "brand";

function App() {
  const [medications, setMedications] = useState<Medication[]>([]);
  const [stockInMedicationId, setStockInMedicationId] =
    useState<number | null>(null);
  const [stockOutMedicationId, setStockOutMedicationId] =
    useState<number | null>(null);
  const [historyMedicationId, setHistoryMedicationId] =
    useState<number | null>(null);
  const [editingMedication, setEditingMedication] =
    useState<Medication | null>(null);
  const [medicationToDelete, setMedicationToDelete] =
    useState<Medication | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<SortOption>("name");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  function handleMedicationCreated(medication: Medication) {
  setMedications((previous) => [...previous, medication]);
}
  function handleMedicationUpdated(updatedMedication: Medication) {
    setMedications((previous) =>
      previous.map((medication) =>
        medication.id === updatedMedication.id
          ? updatedMedication
          : medication
      )
    );

    setEditingMedication(null);
  }

  async function handleStockInSuccess() {
  try {
    const updatedMedications = await getMedications();

    setMedications(updatedMedications);
    setError(null);
    setStockInMedicationId(null);
  } catch {
    setError(
      "Stock was added, but the medication list could not be refreshed."
    );
  }
}

  async function handleStockOutSuccess() {
    try {
      const updatedMedications = await getMedications();

      setMedications(updatedMedications);
      setError(null);
      setStockOutMedicationId(null);
    } catch {
      setError(
        "Stock was removed, but the medication list could not be refreshed."
      );
    }
  }

  async function handleMedicationDeleted() {
    if (!medicationToDelete || deleting) {
      return;
    }

    const medicationId = medicationToDelete.id;

    setDeleting(true);
    setDeleteError(null);

    try {
      await deleteMedication(medicationId);

      // Remove the deleted record from the React table.
      setMedications((previous) =>
        previous.filter(
          (medication) => medication.id !== medicationId
        )
      );

      // Close the confirmation dialog.
      setMedicationToDelete(null);

      // Close the edit form if the same medication was open.
      setEditingMedication((previous) =>
        previous?.id === medicationId ? null : previous
      );
    } catch (error) {
      setDeleteError(
        error instanceof Error
          ? error.message
          : "Unable to delete medication."
      );
    } finally {
      setDeleting(false);
    }
  }


  useEffect(() => {
    let active = true;

    async function loadMedications() {
      try {
        const data = await getMedications();

        if (active) {
          setMedications(data);
          setError(null);
        }
      } catch {
        if (active) {
          setError("Unable to load medications from the API.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadMedications();

    return () => {
      active = false;
    };
  }, []);

  const filteredMedications = medications
    .filter((medication) => {
      const query = search.trim().toLowerCase();

      return (
        medication.name.toLowerCase().includes(query) ||
        medication.brand.toLowerCase().includes(query)
      );
    })
    .sort((a, b) =>
      a[sortBy].localeCompare(b[sortBy])
    );

  return (
    <main>
      <h1>Medication Inventory</h1>

      <p>Manage and review medication inventory records.</p>

      <MedicationForm onMedicationCreated={handleMedicationCreated} />

      {editingMedication && (
        <EditMedicationForm
          key={editingMedication.id}
          medication={editingMedication}
          onMedicationUpdated={handleMedicationUpdated}
          onCancel={() => setEditingMedication(null)}
        />
      )}

      <div>
        <label htmlFor="medication-search">
          Search medications
        </label>

        <input
          id="medication-search"
          type="text"
          placeholder="Search by name or brand"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
      </div>

      <div>
        <label htmlFor="medication-sort">
          Sort by
        </label>

        <select
          id="medication-sort"
          value={sortBy}
          onChange={(event) =>
            setSortBy(event.target.value as SortOption)
          }
        >
          <option value="name">Name</option>
          <option value="brand">Brand</option>
        </select>
      </div>

      {loading && <p>Loading medications...</p>}

      {error && <p role="alert">{error}</p>}

      {!loading && !error && (
        <>
          <p>Total medications: {filteredMedications.length}</p>

          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Brand</th>
                <th>NDC</th>
                <th>Expiration Date</th>
                <th>Lot Number</th>
                <th>Quantity</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>           
              {filteredMedications.map((medication) => (
                <tr key={medication.id}>
                  <td>{medication.name}</td>
                  <td>{medication.brand}</td>
                  <td>{medication.ndc}</td>
                  <td>{medication.expiration_date}</td>
                  <td>{medication.lot_number}</td>
                  <td>{medication.quantity}</td>                      
                  <td>
                    <button
                      type="button"
                      onClick={() => setEditingMedication(medication)}
                    >
                      Edit
                    </button>

                    {" "}

                    <button
                      type="button"
                      disabled={deleting}
                      onClick={() => {
                        setDeleteError(null);
                        setMedicationToDelete(medication);
                      }}
                    >
                      Delete
                    </button>

                    {" "}

                    <button
                      type="button"
                      onClick={() => {
                        setStockOutMedicationId(null);

                        setStockInMedicationId((previous) =>
                          previous === medication.id ? null : medication.id
                        );
                      }}
                    >
                      {stockInMedicationId === medication.id
                        ? "Close Stock IN"
                        : "Stock IN"}
                    </button>

                    {" "}

                    <button
                      type="button"
                      onClick={() => {
                          setStockOutMedicationId(null);
                          setHistoryMedicationId(null);

                          setStockInMedicationId((previous) =>
                            previous === medication.id ? null : medication.id
                          );
                        }}
                    >
                      {stockOutMedicationId === medication.id
                        ? "Close Stock OUT"
                        : "Stock OUT"}
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setStockInMedicationId(null);
                        setHistoryMedicationId(null);

                        setStockOutMedicationId((previous) =>
                          previous === medication.id ? null : medication.id
                        );
                      }}
                    >
                      {historyMedicationId === medication.id
                        ? "Close History"
                        : "History"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {medicationToDelete && (
            <div
              role="dialog"
              aria-modal="true"
              aria-labelledby="delete-dialog-title"
              style={{
                border: "1px solid #999",
                borderRadius: "8px",
                padding: "20px",
                marginTop: "20px",
              }}
            >
              <h2 id="delete-dialog-title">
                Confirm Medication Deletion
              </h2>

              <p>
                Are you sure you want to delete{" "}
                <strong>{medicationToDelete.name}</strong>?
              </p>

              <p>
                NDC: {medicationToDelete.ndc}
              </p>

              <p>
                Lot Number: {medicationToDelete.lot_number}
              </p>

              <p>
                This action cannot be undone.
              </p>
      
              {deleteError && (
                <p role="alert">{deleteError}</p>
              )}

              <button
                type="button"
                disabled={deleting}
                onClick={() => {
                  setMedicationToDelete(null);
                  setDeleteError(null);
                }}
              >
                Cancel
              </button>

              {" "}

              <button
                type="button"
                disabled={deleting}
                onClick={handleMedicationDeleted}
              >
                {deleting ? "Deleting..." : "Confirm Delete"}
              </button>
            </div>
          )}
          {stockInMedicationId !== null && (() => {
            const selectedMedication = medications.find(
              (medication) => medication.id === stockInMedicationId
            );

            if (!selectedMedication) {
              return null;
            }

            return (
              <section aria-label="Stock IN form">
                <StockInForm
                  key={selectedMedication.id}
                  medicationId={selectedMedication.id}
                  medicationName={selectedMedication.name}
                  onSuccess={handleStockInSuccess}
                />

                <button
                  type="button"
                  onClick={() => setStockInMedicationId(null)}
                >
                  Cancel Stock IN
                </button>
              </section>
            );
          })()}
          {stockOutMedicationId !== null && (() => {
            const selectedMedication = medications.find(
              (medication) => medication.id === stockOutMedicationId
            );

            if (!selectedMedication) {
              return null;
            }

            return (
              <section aria-label="Stock OUT form">
                <StockOutForm
                  key={selectedMedication.id}
                  medicationId={selectedMedication.id}
                  medicationName={selectedMedication.name}
                  availableQuantity={selectedMedication.quantity}
                  onSuccess={handleStockOutSuccess}
                />

                <button
                  type="button"
                  onClick={() => setStockOutMedicationId(null)}
                >
                  Cancel Stock OUT
                </button>
              </section>
            );
          })()}
          {historyMedicationId !== null && (() => {
            const selectedMedication = medications.find(
              (medication) => medication.id === historyMedicationId
            );

            if (!selectedMedication) {
              return null;
            }

            return (
              <section aria-label="Transaction history panel">
                <TransactionHistory
                  key={selectedMedication.id}
                  medicationId={selectedMedication.id}
                  medicationName={selectedMedication.name}
                />

                <button
                  type="button"
                  onClick={() => setHistoryMedicationId(null)}
                >
                  Close Transaction History
                </button>
              </section>
            );
          })()}
          {filteredMedications.length === 0 && (
            <p>No medications found.</p>
          )}
        </>
      )}
    </main>
  );
}

export default App;
