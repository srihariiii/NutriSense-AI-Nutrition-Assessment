import { useEffect, useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import {
  clearAuth,
  fetchHealthProfile,
  fetchProfile,
  getToken,
  getUser,
} from "../api/api";

export default function Dashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(getUser());
  const [healthProfile, setHealthProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      navigate("/login");
      return;
    }

    Promise.all([fetchProfile(), fetchHealthProfile()])
      .then(([userData, profileData]) => {
        setUser(userData);
        setHealthProfile(profileData);
      })
      .catch((err) => {
        if (
          err.message.includes("Health profile not found") ||
          err.message.includes("404")
        ) {
          navigate("/health-profile");
          return;
        }
        clearAuth();
        navigate("/login");
      })
      .finally(() => setLoading(false));
  }, [navigate]);

  function handleLogout() {
    clearAuth();
    navigate("/login");
  }

  const links = [
    { to: "/dashboard", label: "Dashboard", icon: "📊" },
    { to: "/food-diary", label: "Food diary", icon: "📝" },
    { to: "/symptoms", label: "Symptoms", icon: "🩺" },
    { to: "/lab-results", label: "Lab results", icon: "🔬" },
    { to: "/assessment", label: "Assessment", icon: "📋" },
    { to: "/meal-plan", label: "Meal plan", icon: "🍽️" },
    { to: "/progress", label: "Progress", icon: "📈" },
  ];

  if (loading) {
    return (
      <div className="diary-layout">
        <aside className="diary-sidebar">
          <div className="diary-brand">NutriSense</div>
        </aside>
        <main className="diary-main">
          <p className="loading-text">Loading your dashboard...</p>
        </main>
      </div>
    );
  }

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
      <main className="diary-main">
        <div className="diary-page-header">
          <h1>Dashboard</h1>
          <p>Welcome back, {user?.first_name} {user?.last_name}!</p>
        </div>

        <div className="diary-content" style={{ gridTemplateColumns: "1fr", maxWidth: "760px" }}>
          {healthProfile && (
            <div className="diary-form-panel">
              <h2>Your Nutrition Profile</h2>
              <div className="dashboard-grid">
                <div className="dashboard-stat">
                  <span className="stat-label">Age</span>
                  <span className="stat-value">{healthProfile.age}</span>
                </div>
                <div className="dashboard-stat">
                  <span className="stat-label">Sex</span>
                  <span className="stat-value">{healthProfile.sex}</span>
                </div>
                <div className="dashboard-stat">
                  <span className="stat-label">Height</span>
                  <span className="stat-value">{healthProfile.height_cm} cm</span>
                </div>
                <div className="dashboard-stat">
                  <span className="stat-label">Weight</span>
                  <span className="stat-value">{healthProfile.weight_kg} kg</span>
                </div>
                <div className="dashboard-stat dashboard-stat-wide">
                  <span className="stat-label">Activity Level</span>
                  <span className="stat-value">{healthProfile.activity_level}</span>
                </div>
                <div className="dashboard-stat dashboard-stat-wide">
                  <span className="stat-label">Health Goal</span>
                  <span className="stat-value">{healthProfile.health_goal}</span>
                </div>
              </div>

              {healthProfile.dietary_restrictions?.length > 0 && (
                <div className="dashboard-restrictions" style={{ marginTop: "1rem" }}>
                  {healthProfile.dietary_restrictions.map((item) => (
                    <span key={item} className="chip chip-active chip-readonly">
                      {item}
                    </span>
                  ))}
                </div>
              )}

              <div style={{ marginTop: "1.5rem" }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ maxWidth: "220px" }}
                  onClick={() => navigate("/health-profile")}
                >
                  Edit health profile
                </button>
              </div>
            </div>
          )}

          {/* Database Resources Section */}
          <div className="db-resources-card" style={{ marginTop: "1.5rem" }}>
            <h3>📚 Resources</h3>
            <div className="db-resources-links">
              <a href="https://ifct2017.github.io/" target="_blank" rel="noopener noreferrer" className="db-resource-item">
                <span className="resource-icon">🌐</span>
                <div>
                  <strong>IFCT 2017 Dataset</strong>
                  <p>Indian Food Composition Tables — NIN Hyderabad (542 items)</p>
                </div>
              </a>
              <a href="https://fdc.nal.usda.gov/" target="_blank" rel="noopener noreferrer" className="db-resource-item">
                <span className="resource-icon">🇺🇸</span>
                <div>
                  <strong>USDA FoodData Central</strong>
                  <p>U.S. Department of Agriculture Food Catalog (8,151 items)</p>
                </div>
              </a>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
