import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import {
  clearAuth,
  fetchProfile,
  getToken,
  getUser,
  fetchAssessmentStatus,
  fetchLatestAssessment,
} from "../api/api";

const DEFAULT_RISKS = [
  { label: "label_calcium", nutrient_name: "Calcium", percentage: 95, level: "HIGH", tag: "Low calcium intake" },
  { label: "label_vitamin_b12", nutrient_name: "Vitamin B12", percentage: 94, level: "HIGH", tag: "Low B12 intake" },
  { label: "label_vitamin_a", nutrient_name: "Vitamin A", percentage: 92, level: "HIGH", tag: "Low vitamin A intake" },
  { label: "label_vitamin_d", nutrient_name: "Vitamin D", percentage: 43, level: "MODERATE", tag: "Low vitamin D intake" },
  { label: "label_iron", nutrient_name: "Iron", percentage: 17, level: "LOW", tag: "Low iron intake" },
  { label: "label_zinc", nutrient_name: "Zinc", percentage: 9, level: "LOW", tag: "Low zinc intake" },
  { label: "label_protein", nutrient_name: "Protein", percentage: 8, level: "LOW", tag: "Low protein intake" },
  { label: "label_vitamin_c", nutrient_name: "Vitamin C", percentage: 4, level: "LOW", tag: "Low vitamin C intake" },
  { label: "label_folate", nutrient_name: "Folate", percentage: 4, level: "LOW", tag: "Low folate intake" },
  { label: "label_magnesium", nutrient_name: "Magnesium", percentage: 4, level: "LOW", tag: "Low magnesium intake" },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(getUser());
  const [loading, setLoading] = useState(false);
  const [consecutiveDays, setConsecutiveDays] = useState(4);
  const [wellnessScore, setWellnessScore] = useState(62.9);
  const [riskList, setRiskList] = useState(DEFAULT_RISKS);
  const [hasRealAssessment, setHasRealAssessment] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      navigate("/login");
      return;
    }

    // Quick parallel load
    Promise.all([
      fetchProfile().catch(() => null),
      fetchAssessmentStatus().catch(() => null),
      fetchLatestAssessment().catch(() => null),
    ])
      .then(([userData, statusData, latestData]) => {
        if (userData) setUser(userData);
        if (statusData) {
          setConsecutiveDays(statusData.consecutive_days ?? statusData.consecutive_days_logged ?? 0);
        }
        if (latestData) {
          if (typeof latestData.wellness_score === "number" && latestData.wellness_score > 0) {
            setWellnessScore(latestData.wellness_score);
          }
          if (Array.isArray(latestData.risk_items) && latestData.risk_items.length > 0) {
            setRiskList(latestData.risk_items);
            setHasRealAssessment(true);
          } else if (Array.isArray(latestData.risks) && latestData.risks.length > 0) {
            setRiskList(latestData.risks);
            setHasRealAssessment(true);
          }
        }
      })
      .finally(() => setLoading(false));
  }, [navigate]);

  function handleLogout() {
    clearAuth();
    navigate("/login");
  }

  return (
    <div className="diary-layout">
      {/* Sidebar with Desktop Sticky & Mobile Drawer */}
      <Sidebar user={user} onLogout={handleLogout} />

      {/* Main Dashboard Content */}
      <main className="diary-main dashboard-page-bg">
        <div className="dashboard-header-container">
          <h1 className="dash-title">Dashboard</h1>
          <p className="dash-subtitle">Your nutrition snapshot from logged meals.</p>
        </div>

        <div className="dash-body-grid">
          {/* Top Row Cards */}
          <div className="dash-top-row">
            {/* Diary Status Card */}
            <div className="dash-card">
              <h3 className="dash-card-title">Diary status</h3>
              <p className="dash-days-num">{consecutiveDays} days logged</p>
              <div className="dash-actions-row">
                <button
                  type="button"
                  className="btn-dash-outline"
                  onClick={() => navigate("/food-diary")}
                >
                  Log a meal
                </button>
                <button
                  type="button"
                  className="btn-dash-primary"
                  onClick={() => navigate("/assessment")}
                >
                  Run assessment
                </button>
              </div>
            </div>

            {/* Latest Wellness Score Card */}
            <div className="dash-card">
              <h3 className="dash-card-title">Latest wellness score</h3>
              <div className="dash-score-container">
                <span className="dash-score-val">{wellnessScore}%</span>
              </div>
              <p className="dash-score-sub">From your last assessment</p>
            </div>
          </div>

          {/* Bottom Card: Nutrient Deficiency Risks */}
          <div className="dash-card dash-risks-card" style={{ maxWidth: "100%" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.25rem" }}>
              <h3 className="dash-card-title" style={{ margin: 0 }}>
                Nutrient Deficiency Risks
              </h3>
              <span className="risk-count" style={{ fontSize: "0.85rem", fontWeight: "600" }}>
                10 Evaluated
              </span>
            </div>

            <div className="unique-risk-grid">
              {riskList.map((item) => {
                const pct = typeof item.percentage === "number" ? item.percentage : 0;
                const lvl = (item.level || (pct > 65 ? "HIGH" : pct >= 35 ? "MODERATE" : "LOW")).toLowerCase();
                const nutName = item.nutrient_name || item.label?.replace("label_", "").toUpperCase() || "Nutrient";
                const tagText = item.tag || `Low ${nutName.toLowerCase()} intake`;

                return (
                  <div key={item.label || nutName} className={`unique-risk-card ${lvl}`}>
                    <div className="risk-card-top">
                      <span className="risk-card-name">{nutName}</span>
                      <span className={`risk-badge-tag ${lvl}`}>
                        {pct}% {lvl.toUpperCase()}
                      </span>
                    </div>

                    <div className="risk-meter-track">
                      <div
                        className={`risk-meter-fill ${lvl}`}
                        style={{ width: `${Math.max(6, Math.min(pct, 100))}%` }}
                      ></div>
                    </div>

                    <div className="risk-card-bottom">
                      <span className="rda-tag">{tagText}</span>
                      {item.lab_boosted && (
                        <span className="lab-boost-badge">
                          🔬 {item.lab_notes || "Lab Boosted"}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

