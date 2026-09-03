import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import {
  clearAuth,
  fetchProfile,
  getToken,
  getUser,
  fetchMealPlan,
  regenerateMealPlan,
} from "../api/api";

const DAYS_META = [
  { key: "Sun", label: "Sun", fullName: "Sunday" },
  { key: "Mon", label: "Mon", fullName: "Monday" },
  { key: "Tue", label: "Tue", fullName: "Tuesday" },
  { key: "Wed", label: "Wed", fullName: "Wednesday" },
  { key: "Thu", label: "Thu", fullName: "Thursday" },
  { key: "Fri", label: "Fri", fullName: "Friday" },
  { key: "Sat", label: "Sat", fullName: "Saturday" },
];

export default function MealPlan() {
  const navigate = useNavigate();
  const [user, setUser] = useState(getUser());
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [mealPlan, setMealPlan] = useState(null);
  const [activeDayKey, setActiveDayKey] = useState("Sun");

  useEffect(() => {
    const token = getToken();
    if (!token) {
      navigate("/login");
      return;
    }

    fetchProfile()
      .then((userData) => setUser(userData))
      .catch(() => null);

    loadPlan();
  }, [navigate]);

  const loadPlan = async () => {
    setLoading(true);
    try {
      const data = await fetchMealPlan();
      setMealPlan(data);
    } catch (err) {
      console.error("Failed to load meal plan:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerate = async () => {
    setGenerating(true);
    try {
      const data = await regenerateMealPlan();
      setMealPlan(data);
    } catch (err) {
      console.error("Failed to regenerate meal plan:", err);
    } finally {
      setGenerating(false);
    }
  };

  const handleLogout = () => {
    clearAuth();
    navigate("/login");
  };

  const links = [
    { to: "/dashboard", label: "Dashboard", icon: "📊" },
    { to: "/food-diary", label: "Food diary", icon: "📝" },
    { to: "/lab-results", label: "Lab results", icon: "🔬" },
    { to: "/assessment", label: "Assessment", icon: "📋" },
    { to: "/meal-plan", label: "Meal plan", icon: "🍽️" },
    { to: "/progress", label: "Progress", icon: "📈" },
    { to: "/profile", label: "Profile", icon: "⚙️" },
  ];

  const activeDayObj = mealPlan?.days?.find((d) => d.day_key === activeDayKey) || mealPlan?.days?.[0];

  if (loading) {
    return (
      <div className="diary-layout">
        <aside className="diary-sidebar">
          <div className="diary-brand">NutriSense</div>
        </aside>
        <main className="diary-main meal-plan-page-bg">
          <p className="loading-text">Loading 7-day meal plan...</p>
        </main>
      </div>
    );
  }

  const focusStr = mealPlan?.focus_nutrients?.join(", ") || "calcium, vitamin_b12, vitamin_a, vitamin_d";
  const dietStr = mealPlan?.dietary_restrictions?.join(", ") || "Vegetarian, Dairy-free";

  return (
    <div className="diary-layout">
      {/* Sidebar with Desktop Sticky & Mobile Drawer */}
      <Sidebar user={user} onLogout={handleLogout} />

      {/* Main Meal Plan Content */}
      <main className="diary-main meal-plan-page-bg">
        <div className="meal-plan-header-row">
          <div>
            <h1 className="meal-plan-title">7-day meal plan</h1>
            <p className="meal-plan-subtitle">
              Rule-based plan (Approach A) targeting your top deficiencies.
            </p>
          </div>
          <button
            type="button"
            className="btn-regenerate-plan"
            onClick={handleRegenerate}
            disabled={generating}
          >
            {generating ? "Regenerating..." : "Regenerate plan"}
          </button>
        </div>

        {/* Focus & Diet Info Bar */}
        <div className="meal-plan-focus-bar">
          <span>Focus: <strong>{focusStr}</strong></span>
          <span className="dot-sep">•</span>
          <span>Diet: <strong>{dietStr}</strong></span>
        </div>

        {/* Day Tabs */}
        <div className="meal-plan-day-tabs">
          {DAYS_META.map((d) => (
            <button
              key={d.key}
              type="button"
              className={`day-tab-btn ${activeDayKey === d.key ? "active" : ""}`}
              onClick={() => setActiveDayKey(d.key)}
            >
              {d.label}
            </button>
          ))}
        </div>

        {/* Meal Plan Card for Active Day */}
        <div className="meal-plan-card">
          <h2 className="day-card-heading">{activeDayObj?.day_name || "Sunday"}</h2>

          <div className="meals-list">
            {activeDayObj?.meals?.map((m) => (
              <div key={m.meal_type} className="meal-section">
                <h4 className="meal-type-title">{m.meal_type}</h4>
                <p className="meal-food-title">{m.food_title}</p>
                <p className="meal-target-summary">{m.target_summary}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}
