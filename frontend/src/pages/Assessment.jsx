import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import {
  clearAuth,
  fetchLatestAssessment,
  getUser,
  runAssessment,
} from "../api/api";

export default function AssessmentPage() {
  const navigate = useNavigate();
  const user = getUser();

  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [successMsg, setSuccessMsg] = useState("");
  const [assessmentData, setAssessmentData] = useState({
    wellness_score: 0,
    distinct_days: 0,
    consecutive_days: 0,
    can_run_assessment: false,
    risk_items: [],
    recommended_groups: [],
  });

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setErrorMsg("");
    try {
      const data = await fetchLatestAssessment();
      setAssessmentData(data);
    } catch (err) {
      setErrorMsg(err.message || "Failed to load assessment data.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRunAssessment() {
    setErrorMsg("");
    setSuccessMsg("");
    setRunning(true);

    try {
      const data = await runAssessment();
      setAssessmentData(data);
      setSuccessMsg("Assessment calculated successfully using Random Forest ML model!");
    } catch (err) {
      const msg = err.message || "Enter the atlest 4 concecutive days";
      setErrorMsg(msg);
    } finally {
      setRunning(false);
    }
  }

  function handleSignOut() {
    clearAuth();
    navigate("/login");
  }

  const score = assessmentData.wellness_score || 0;
  const scoreColor =
    score >= 75 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";

  return (
    <div className="diary-layout">
      {/* Sidebar with Desktop Sticky & Mobile Drawer */}
      <Sidebar user={user} onLogout={handleSignOut} />

      {/* Main Content Area */}
      <main className="diary-main assessment-main-container">
        {/* Top Floating Glass Header */}
        <header className="assessment-top-header">
          <div className="header-meta-group">
            <span className="model-chip">🤖 Random Forest Model</span>
            <span className="days-chip">
              🗓️ {assessmentData.consecutive_days}/4 Consecutive Days Logged (min 4 required)
            </span>
          </div>

          <button
            onClick={handleRunAssessment}
            disabled={running}
            className="run-ai-assessment-btn"
          >
            {running ? "Analyzing ML Data..." : "Run AI Assessment"}
          </button>
        </header>

        {/* Alerts */}
        {errorMsg && (
          <div className="unique-alert error-alert">
            <span className="alert-icon">⚠️</span>
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div className="unique-alert success-alert">
            <span className="alert-icon">✨</span>
            <span>{successMsg}</span>
          </div>
        )}

        {loading ? (
          <div className="loading-spinner-container">
            <div className="spinner"></div>
            <p>Initializing AI Nutrient Assessment...</p>
          </div>
        ) : (
          <div className="assessment-content-flow">
            {/* Top Hero Banner: Overall Wellness Score */}
            <section className="wellness-hero-card">
              <div className="hero-score-ring" style={{ "--score-color": scoreColor }}>
                <div className="score-inner">
                  <span className="score-number">{score}%</span>
                  <span className="score-label">Wellness Index</span>
                </div>
              </div>

              <div className="hero-text-content">
                <h1 className="hero-title">Nutritional Assessment Report</h1>
                <p className="hero-description">
                  AI MultiOutput Random Forest Classifier trained on NHANES dataset. Evaluates 13 biomarker inputs to compute deficiency risk probabilities across 10 vital nutrients.
                </p>
                <div className="hero-badges-row">
                  <span className="badge-pill green">✓ 13 Features Evaluated</span>
                  <span className="badge-pill teal">✓ Lab Results Calibrated</span>
                  <span className="badge-pill mint">✓ 8,730+ Food Recommender</span>
                </div>
              </div>
            </section>

            {/* Middle Section: Deficiency Risks Grid & Recommendations */}
            <div className="assessment-two-column-layout">
              {/* Left Column: Deficiency Risks */}
              <div className="assessment-glass-panel risks-panel">
                <div className="panel-title-bar">
                  <h2>Nutrient Deficiency Risks</h2>
                  <span className="risk-count">
                    {assessmentData.risk_items.length} Evaluated
                  </span>
                </div>

                {assessmentData.risk_items.length === 0 ? (
                  <div className="empty-assessment-state">
                    <p className="empty-title">No Assessment Generated Yet</p>
                    <p className="empty-desc">
                      Log 7 consecutive days in your food diary with all 4 meal types (Breakfast, Lunch, Dinner, Snack) to unlock your full AI Assessment.
                    </p>
                  </div>
                ) : (
                  <div className="unique-risk-grid">
                    {assessmentData.risk_items.map((item) => {
                      const lvl = (item.level || "").toLowerCase();
                      const nutName = item.nutrient_name || item.label;
                      const tagText = lvl === "low"
                        ? `Adequate ${nutName.toLowerCase()} intake`
                        : lvl === "moderate"
                        ? `Moderate ${nutName.toLowerCase()} intake`
                        : (item.tag && item.tag.toLowerCase().includes("low"))
                        ? item.tag
                        : `Low ${nutName.toLowerCase()} intake`;

                      return (
                        <div key={item.label} className={`unique-risk-card ${lvl}`}>
                          <div className="risk-card-top">
                            <span className="risk-card-name">{item.nutrient_name}</span>
                            <span className={`risk-badge-tag ${lvl}`}>
                              {item.percentage}% {item.level}
                            </span>
                          </div>

                          <div className="risk-meter-track">
                            <div
                              className={`risk-meter-fill ${lvl}`}
                              style={{ width: `${Math.max(6, item.percentage)}%` }}
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
                )}
              </div>

              {/* Right Column: Recommended Foods */}
              <div className="assessment-glass-panel recs-panel">
                <div className="panel-title-bar">
                  <h2>Recommended Foods</h2>
                  <span className="rec-subhead">Rich Nutrient Sources</span>
                </div>

                {assessmentData.recommended_groups.length === 0 ? (
                  <div className="empty-text-box">
                    Run an assessment to view custom dietary recommendations.
                  </div>
                ) : (
                  <div className="recs-group-container">
                    {assessmentData.recommended_groups.map((group) => (
                      <div key={group.nutrient_name} className="unique-rec-group">
                        <div className="group-header">
                          <span className="group-icon">🥑</span>
                          <h3>{group.nutrient_name} Rich Foods</h3>
                        </div>

                        <div className="food-cards-list">
                          {group.foods.map((food) => (
                            <div key={food.id} className="food-micro-card">
                              <span className="micro-food-name" title={food.name}>{food.name}</span>
                              <div className="micro-food-stats">
                                <span className="stat-pill">
                                  {food.target_display || (food.iron_mg > 0 ? `Fe ${food.iron_mg}mg` : `Ca ${food.calcium_mg}mg`)}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
