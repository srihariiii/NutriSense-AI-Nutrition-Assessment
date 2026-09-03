import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import {
  clearAuth,
  getUser,
  getToken,
  saveAuth,
  fetchProfile,
  fetchHealthProfile,
  saveHealthProfile,
  updateAccount,
} from "../api/api";

const DIETARY_OPTIONS = [
  "Vegetarian",
  "Vegan",
  "Gluten-free",
  "Dairy-free",
  "Nut allergy",
  "None",
];

export default function Profile() {
  const navigate = useNavigate();
  const currentUser = getUser();

  // Account Settings Form State
  const [accountForm, setAccountForm] = useState({
    full_name: currentUser
      ? `${currentUser.first_name || ""} ${currentUser.last_name || ""}`.trim()
      : "",
    email: currentUser?.email || "",
    current_password: "",
    new_password: "",
    confirm_new_password: "",
  });

  // Health Profile Form State
  const [healthForm, setHealthForm] = useState({
    age: "",
    sex: "Male",
    height_cm: "",
    weight_kg: "",
    activity_level: "Lightly active",
    health_goal: "Improve energy",
    dietary_restrictions: ["Vegetarian"],
  });

  const [accountMsg, setAccountMsg] = useState("");
  const [accountError, setAccountError] = useState("");
  const [healthMsg, setHealthMsg] = useState("");
  const [healthError, setHealthError] = useState("");
  const [loadingAccount, setLoadingAccount] = useState(false);
  const [loadingHealth, setLoadingHealth] = useState(false);

  useEffect(() => {
    if (!currentUser) {
      navigate("/login");
      return;
    }
    loadUserData();
    loadHealthData();
  }, [navigate]);

  const loadUserData = async () => {
    try {
      const user = await fetchProfile();
      if (user) {
        setAccountForm((prev) => ({
          ...prev,
          full_name: `${user.first_name || ""} ${user.last_name || ""}`.trim(),
          email: user.email || "",
        }));
        saveAuth(getToken(), user);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadHealthData = async () => {
    try {
      const data = await fetchHealthProfile();
      if (data) {
        setHealthForm({
          age: data.age ?? "",
          sex: data.sex || "Male",
          height_cm: data.height_cm ?? "",
          weight_kg: data.weight_kg ?? "",
          activity_level: data.activity_level || "Lightly active",
          health_goal: data.health_goal || "Improve energy",
          dietary_restrictions: Array.isArray(data.dietary_restrictions)
            ? data.dietary_restrictions
            : [data.dietary_restrictions || "None"],
        });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAccountChange = (e) => {
    setAccountForm({ ...accountForm, [e.target.name]: e.target.value });
  };

  const handleHealthChange = (e) => {
    setHealthForm({ ...healthForm, [e.target.name]: e.target.value });
  };

  const toggleRestriction = (option) => {
    let updated = [...healthForm.dietary_restrictions];
    if (option === "None") {
      updated = ["None"];
    } else {
      updated = updated.filter((r) => r !== "None");
      if (updated.includes(option)) {
        updated = updated.filter((r) => r !== option);
      } else {
        updated.push(option);
      }
      if (updated.length === 0) updated = ["None"];
    }
    setHealthForm({ ...healthForm, dietary_restrictions: updated });
  };

  const handleSaveAccount = async (e) => {
    e.preventDefault();
    setAccountMsg("");
    setAccountError("");
    setLoadingAccount(true);

    try {
      const updatedUser = await updateAccount(accountForm);
      // Update local storage user details with existing token
      saveAuth(getToken(), updatedUser);
      setAccountMsg("Account settings saved successfully!");
      setAccountForm((prev) => ({
        ...prev,
        current_password: "",
        new_password: "",
        confirm_new_password: "",
      }));
      setTimeout(() => setAccountMsg(""), 4000);
    } catch (err) {
      setAccountError(err.message || "Failed to update account settings.");
    } finally {
      setLoadingAccount(false);
    }
  };

  const handleSaveHealth = async (e) => {
    e.preventDefault();
    setHealthMsg("");
    setHealthError("");
    setLoadingHealth(true);

    try {
      const payload = {
        age: parseInt(healthForm.age, 10),
        sex: healthForm.sex,
        height_cm: parseFloat(healthForm.height_cm),
        weight_kg: parseFloat(healthForm.weight_kg),
        activity_level: healthForm.activity_level,
        health_goal: healthForm.health_goal,
        dietary_restrictions: healthForm.dietary_restrictions,
      };
      await saveHealthProfile(payload);
      setHealthMsg("Health profile updated successfully!");
      setTimeout(() => setHealthMsg(""), 4000);
    } catch (err) {
      setHealthError(err.message || "Failed to update health profile.");
    } finally {
      setLoadingHealth(false);
    }
  };

  const handleLogout = () => {
    clearAuth();
    navigate("/login");
  };

  return (
    <div className="diary-layout profile-page-bg">
      {/* Sidebar with Desktop Sticky & Mobile Drawer */}
      <Sidebar user={currentUser} onLogout={handleLogout} />

      {/* Main Content */}
      <main className="diary-main profile-main-container">
        <div className="profile-top-banner">
          <div>
            <h1 className="profile-page-title">Profile & Settings</h1>
            <p className="profile-page-subtitle">
              Manage your personal account credentials and health profile parameters used by NutriSense AI models.
            </p>
          </div>
          <span className="profile-badge">⚙️ Account Settings</span>
        </div>

        {/* Two Column Grid Layout */}
        <div className="profile-two-column-grid">
          {/* Left Panel - Account Settings */}
          <div className="profile-card-panel">
            <div className="card-panel-header">
              <h2>Account Settings</h2>
              <p>You can update name or email anytime. Current password is only needed to set a new password.</p>
            </div>

            {accountMsg && <div className="profile-toast success">✅ {accountMsg}</div>}
            {accountError && <div className="profile-toast error">⚠️ {accountError}</div>}

            <form onSubmit={handleSaveAccount} className="profile-form">
              <div className="form-group-item">
                <label>Full name</label>
                <input
                  type="text"
                  name="full_name"
                  value={accountForm.full_name}
                  onChange={handleAccountChange}
                  placeholder="Enter full name"
                  required
                  className="profile-input"
                />
              </div>

              <div className="form-group-item">
                <label>Email</label>
                <input
                  type="email"
                  name="email"
                  value={accountForm.email}
                  onChange={handleAccountChange}
                  placeholder="Enter email"
                  required
                  className="profile-input"
                />
              </div>

              <div className="form-group-item">
                <label>Current password</label>
                <input
                  type="password"
                  name="current_password"
                  value={accountForm.current_password}
                  onChange={handleAccountChange}
                  placeholder="Only needed to set a new password"
                  className="profile-input"
                />
              </div>

              <div className="form-group-item">
                <label>New password</label>
                <input
                  type="password"
                  name="new_password"
                  value={accountForm.new_password}
                  onChange={handleAccountChange}
                  placeholder="Leave blank to keep current"
                  className="profile-input"
                />
              </div>

              <div className="form-group-item">
                <label>Confirm new password</label>
                <input
                  type="password"
                  name="confirm_new_password"
                  value={accountForm.confirm_new_password}
                  onChange={handleAccountChange}
                  placeholder="Confirm new password"
                  className="profile-input"
                />
              </div>

              <button type="submit" className="profile-save-btn" disabled={loadingAccount}>
                {loadingAccount ? "Saving..." : "Save account"}
              </button>
            </form>
          </div>

          {/* Right Panel - Health Profile */}
          <div className="profile-card-panel">
            <div className="card-panel-header">
              <h2>Health Profile</h2>
              <p>Same fields as health onboarding — used for assessments and meal filters.</p>
            </div>

            {healthMsg && <div className="profile-toast success">✅ {healthMsg}</div>}
            {healthError && <div className="profile-toast error">⚠️ {healthError}</div>}

            <form onSubmit={handleSaveHealth} className="profile-form">
              <div className="form-group-item">
                <label>Age</label>
                <input
                  type="number"
                  name="age"
                  value={healthForm.age}
                  onChange={handleHealthChange}
                  placeholder="24"
                  required
                  className="profile-input"
                />
              </div>

              <div className="form-group-item">
                <label>Sex</label>
                <select
                  name="sex"
                  value={healthForm.sex}
                  onChange={handleHealthChange}
                  className="profile-select"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>

              <div className="form-group-item">
                <label>Height (cm)</label>
                <input
                  type="number"
                  name="height_cm"
                  value={healthForm.height_cm}
                  onChange={handleHealthChange}
                  placeholder="165"
                  required
                  className="profile-input"
                />
              </div>

              <div className="form-group-item">
                <label>Weight (kg)</label>
                <input
                  type="number"
                  name="weight_kg"
                  value={healthForm.weight_kg}
                  onChange={handleHealthChange}
                  placeholder="60"
                  required
                  className="profile-input"
                />
              </div>

              <div className="form-group-item">
                <label>Activity level</label>
                <select
                  name="activity_level"
                  value={healthForm.activity_level}
                  onChange={handleHealthChange}
                  className="profile-select"
                >
                  <option value="Sedentary">Sedentary</option>
                  <option value="Lightly active">Lightly active</option>
                  <option value="Moderately active">Moderately active</option>
                  <option value="Very active">Very active</option>
                  <option value="Extremely active">Extremely active</option>
                </select>
              </div>

              <div className="form-group-item">
                <label>Health goal</label>
                <input
                  type="text"
                  name="health_goal"
                  value={healthForm.health_goal}
                  onChange={handleHealthChange}
                  placeholder="Improve energy"
                  required
                  className="profile-input"
                />
              </div>

              <div className="form-group-item">
                <label>Dietary restrictions</label>
                <div className="dietary-pills-row">
                  {DIETARY_OPTIONS.map((opt) => {
                    const isSelected = healthForm.dietary_restrictions.includes(opt);
                    return (
                      <button
                        type="button"
                        key={opt}
                        onClick={() => toggleRestriction(opt)}
                        className={`dietary-pill-btn ${isSelected ? "selected" : ""}`}
                      >
                        {opt}
                      </button>
                    );
                  })}
                </div>
              </div>

              <button type="submit" className="profile-save-btn" disabled={loadingHealth}>
                {loadingHealth ? "Saving..." : "Save health profile"}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}
