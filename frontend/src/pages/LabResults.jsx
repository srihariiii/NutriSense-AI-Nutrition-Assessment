import { useState, useEffect } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { clearAuth, getUser, fetchLabResults, saveLabResults } from "../api/api";

export default function LabResults() {
  const navigate = useNavigate();
  const location = useLocation();
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
      setTimeout(() => setStatusMsg(""), 3000);
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

  const links = [
    { to: "/dashboard", label: "Dashboard", icon: "📊" },
    { to: "/food-diary", label: "Food diary", icon: "📝" },
    { to: "/symptoms", label: "Symptoms", icon: "🩺" },
    { to: "/lab-results", label: "Lab results", icon: "🔬" },
    { to: "/assessment", label: "Assessment", icon: "📋" },
    { to: "/meal-plan", label: "Meal plan", icon: "🍽️" },
    { to: "/progress", label: "Progress", icon: "📈" },
  ];

  return (
    <div className="diary-layout">
      {/* Sidebar */}
      <aside className="diary-sidebar">
        <div className="diary-brand">NutriSense</div>
        <div className="sidebar-user">{user?.email}</div>

        <nav className="sidebar-nav">
          {links.map((l) => (
            <Link key={l.to} to={l.to} className={location.pathname === l.to ? "active" : ""}>
              <span className="nav-icon">{l.icon}</span> {l.label}
            </Link>
          ))}
        </nav>

        <button className="sidebar-logout" onClick={handleLogout}>Sign out</button>
      </aside>

      {/* Main Content */}
      <main className="diary-main lab-main-bg">
        <div className="diary-page-header">
          <h1>Lab results</h1>
        </div>

        <div className="lab-results-card">
          <p className="lab-subtitle-note">
            Optional — improves iron &amp; vitamin D confidence after ML prediction.
          </p>

          {statusMsg && (
            <div className={`diary-status ${statusMsg.includes("success") ? "success" : ""}`}>
              {statusMsg}
            </div>
          )}

          <form onSubmit={handleSubmit} className="lab-form">
            <div className="row-2">
              {/* Left Column */}
              <div className="lab-column">
                <div className="form-group">
                  <label htmlFor="hemoglobin">Hemoglobin (g/dL)</label>
                  <input
                    id="hemoglobin"
                    name="hemoglobin"
                    type="number"
                    step="0.1"
                    placeholder="Enter hemoglobin"
                    value={form.hemoglobin}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="ferritin">Ferritin</label>
                  <input
                    id="ferritin"
                    name="ferritin"
                    type="number"
                    step="0.1"
                    placeholder="Enter ferritin"
                    value={form.ferritin}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="calcium">Calcium</label>
                  <input
                    id="calcium"
                    name="calcium"
                    type="number"
                    step="0.1"
                    placeholder="Enter calcium"
                    value={form.calcium}
                    onChange={handleChange}
                  />
                </div>
              </div>

              {/* Right Column */}
              <div className="lab-column">
                <div className="form-group">
                  <label htmlFor="serum_vitamin_d">Serum Vitamin D</label>
                  <input
                    id="serum_vitamin_d"
                    name="serum_vitamin_d"
                    type="number"
                    step="0.1"
                    placeholder="Enter serum vitamin D"
                    value={form.serum_vitamin_d}
                    onChange={handleChange}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="vitamin_b12">Vitamin B12</label>
                  <input
                    id="vitamin_b12"
                    name="vitamin_b12"
                    type="number"
                    step="0.1"
                    placeholder="Enter vitamin B12"
                    value={form.vitamin_b12}
                    onChange={handleChange}
                  />
                </div>
              </div>
            </div>

            <button type="submit" className="btn btn-primary lab-save-btn" disabled={loading}>
              {loading ? "Saving..." : "Save labs"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
