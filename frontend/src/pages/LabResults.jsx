import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { clearAuth, getUser, fetchLabResults, saveLabResults } from "../api/api";

export default function LabResults() {
  const navigate = useNavigate();
  const user = getUser();

  const [form, setForm] = useState({
    hemoglobin: "",
    serum_vitamin_d: "",
    ferritin: "",
    vitamin_b12: "",
    calcium: "",
  });

  const [statusMsg, setStatusMsg] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) {
      navigate("/login");
      return;
    }
    loadLabs();
  }, [navigate]);

  const loadLabs = async () => {
    try {
      const data = await fetchLabResults();
      if (data) {
        setForm({
          hemoglobin: data.hemoglobin ?? "",
          serum_vitamin_d: data.serum_vitamin_d ?? "",
          ferritin: data.ferritin ?? "",
          vitamin_b12: data.vitamin_b12 ?? "",
          calcium: data.calcium ?? "",
        });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setStatusMsg("");
    try {
      const payload = {
        hemoglobin: form.hemoglobin ? parseFloat(form.hemoglobin) : null,
        serum_vitamin_d: form.serum_vitamin_d ? parseFloat(form.serum_vitamin_d) : null,
        ferritin: form.ferritin ? parseFloat(form.ferritin) : null,
        vitamin_b12: form.vitamin_b12 ? parseFloat(form.vitamin_b12) : null,
        calcium: form.calcium ? parseFloat(form.calcium) : null,
      };
      await saveLabResults(payload);
      setStatusMsg("Lab results saved successfully!");
      setTimeout(() => setStatusMsg(""), 4000);
    } catch (err) {
      console.error(err);
      setStatusMsg("Failed to save lab results.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    clearAuth();
    navigate("/login");
  };

  return (
    <div className="diary-layout lab-results-page-bg">
      {/* Sidebar with Desktop Sticky & Mobile Drawer */}
      <Sidebar user={user} onLogout={handleLogout} />

      {/* Main Content */}
      <main className="diary-main lab-main-container">
        <div className="lab-header-banner">
          <div>
            <h1 className="lab-page-title">Biomarker Lab Results</h1>
            <p className="lab-page-subtitle">
              Optional clinical biomarkers to recalibrate AI model risk sensitivity for Iron, Vitamin D, Vitamin B12, and Calcium.
            </p>
          </div>
          <span className="lab-tech-chip">🔬 Clinical Calibration</span>
        </div>

        <div className="unique-lab-card">
          {statusMsg && (
            <div className={`lab-status-toast ${statusMsg.includes("success") ? "success" : "error"}`}>
              {statusMsg.includes("success") ? "✅ " : "⚠️ "}
              {statusMsg}
            </div>
          )}

          <form onSubmit={handleSubmit} className="unique-lab-form">
            <div className="lab-inputs-grid">
              {/* Hemoglobin */}
              <div className="lab-input-card">
                <div className="input-card-header">
                  <span className="biomarker-icon">🩸</span>
                  <label htmlFor="hemoglobin">Hemoglobin (g/dL)</label>
                </div>
                <input
                  id="hemoglobin"
                  name="hemoglobin"
                  type="number"
                  step="0.1"
                  placeholder="Enter hemoglobin"
                  value={form.hemoglobin}
                  onChange={handleChange}
                  className="unique-lab-input"
                />
                <span className="cutoff-hint">Ref Cutoff: F &lt; 12.0 · M &lt; 13.0 g/dL</span>
              </div>

              {/* Ferritin */}
              <div className="lab-input-card">
                <div className="input-card-header">
                  <span className="biomarker-icon">🧪</span>
                  <label htmlFor="ferritin">Ferritin (ng/mL)</label>
                </div>
                <input
                  id="ferritin"
                  name="ferritin"
                  type="number"
                  step="0.1"
                  placeholder="Enter ferritin"
                  value={form.ferritin}
                  onChange={handleChange}
                  className="unique-lab-input"
                />
                <span className="cutoff-hint">Ref Cutoff: &lt; 30.0 ng/mL</span>
              </div>

              {/* Serum Vitamin D */}
              <div className="lab-input-card">
                <div className="input-card-header">
                  <span className="biomarker-icon">☀️</span>
                  <label htmlFor="serum_vitamin_d">Serum Vitamin D (nmol/L)</label>
                </div>
                <input
                  id="serum_vitamin_d"
                  name="serum_vitamin_d"
                  type="number"
                  step="0.1"
                  placeholder="Enter serum vitamin D"
                  value={form.serum_vitamin_d}
                  onChange={handleChange}
                  className="unique-lab-input"
                />
                <span className="cutoff-hint">Ref Cutoff: &lt; 50.0 nmol/L</span>
              </div>

              {/* Vitamin B12 */}
              <div className="lab-input-card">
                <div className="input-card-header">
                  <span className="biomarker-icon">💊</span>
                  <label htmlFor="vitamin_b12">Vitamin B12 (pg/mL)</label>
                </div>
                <input
                  id="vitamin_b12"
                  name="vitamin_b12"
                  type="number"
                  step="0.1"
                  placeholder="Enter vitamin B12"
                  value={form.vitamin_b12}
                  onChange={handleChange}
                  className="unique-lab-input"
                />
                <span className="cutoff-hint">Ref Cutoff: &lt; 200.0 pg/mL</span>
              </div>

              {/* Calcium */}
              <div className="lab-input-card wide">
                <div className="input-card-header">
                  <span className="biomarker-icon">🦴</span>
                  <label htmlFor="calcium">Calcium (mg/dL)</label>
                </div>
                <input
                  id="calcium"
                  name="calcium"
                  type="number"
                  step="0.1"
                  placeholder="Enter calcium"
                  value={form.calcium}
                  onChange={handleChange}
                  className="unique-lab-input"
                />
                <span className="cutoff-hint">Ref Cutoff: &lt; 8.5 mg/dL</span>
              </div>
            </div>

            <button type="submit" className="save-lab-biomarkers-btn" disabled={loading}>
              {loading ? "Saving Biomarkers..." : "Save Lab Biomarkers"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
