import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getToken } from "../api/api";

export default function Landing() {
  const navigate = useNavigate();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    try {
      setIsAuthenticated(Boolean(getToken()));
    } catch {
      setIsAuthenticated(false);
    }
  }, []);

  return (
    <div className="landing-wrapper">
      {/* ── Top Navigation Bar ── */}
      <header className="landing-nav">
        <div className="landing-nav-container">
          <div className="landing-brand" onClick={() => navigate("/")}>
            <span className="brand-leaf-icon">🌱</span>
            <span className="brand-logo-text">NutriSense</span>
          </div>

          <nav className="landing-nav-links">
            <a href="#features">Features</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#nutrients">Nutrients</a>
          </nav>

          <div className="landing-nav-actions">
            {isAuthenticated ? (
              <button
                className="landing-btn landing-btn-primary"
                onClick={() => navigate("/dashboard")}
              >
                Go to Dashboard
              </button>
            ) : (
              <>
                <Link to="/login" className="landing-btn landing-btn-ghost">
                  Sign In
                </Link>
                <Link to="/signup" className="landing-btn landing-btn-primary">
                  Get Started
                </Link>
              </>
            )}
          </div>

          {/* Mobile Hamburger Button */}
          <button
            type="button"
            className="landing-mobile-menu-btn"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle navigation"
          >
            {mobileMenuOpen ? "✕" : "☰"}
          </button>
        </div>

        {/* Mobile Dropdown Menu */}
        {mobileMenuOpen && (
          <div className="landing-mobile-menu-dropdown">
            <a href="#features" onClick={() => setMobileMenuOpen(false)}>
              Features
            </a>
            <a href="#how-it-works" onClick={() => setMobileMenuOpen(false)}>
              How It Works
            </a>
            <a href="#nutrients" onClick={() => setMobileMenuOpen(false)}>
              Nutrients
            </a>
            <div className="landing-mobile-menu-actions">
              {isAuthenticated ? (
                <button
                  className="landing-btn landing-btn-primary"
                  style={{ width: "100%" }}
                  onClick={() => {
                    setMobileMenuOpen(false);
                    navigate("/dashboard");
                  }}
                >
                  Go to Dashboard
                </button>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="landing-btn landing-btn-ghost"
                    style={{ width: "100%", textAlign: "center" }}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/signup"
                    className="landing-btn landing-btn-primary"
                    style={{ width: "100%", textAlign: "center" }}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Get Started
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </header>

      {/* ── Hero Section ── */}
      <section className="landing-hero-section">
        <div className="landing-hero-overlay"></div>
        <div className="landing-hero-container">
          <div className="landing-hero-content">
            <div className="hero-pill-badge">
              <span className="hero-sparkle">✨</span>
              <span>Precision Nutrition & AI Assessment</span>
            </div>

            <h1 className="landing-hero-title">
              Precision Nutrition Intelligence, <span className="hero-gradient-highlight">Reimagined by Clinical AI</span>
            </h1>

            <p className="landing-hero-description">
              Detect nutrient deficiency risks from your daily food intake and lab biomarkers with machine learning, and receive personalized, diet-compliant meal recommendations tailored to your health goals.
            </p>

            <div className="landing-hero-cta-group">
              {isAuthenticated ? (
                <button
                  className="landing-btn-hero-primary"
                  onClick={() => navigate("/dashboard")}
                >
                  Open Dashboard <span>→</span>
                </button>
              ) : (
                <>
                  <Link to="/signup" className="landing-btn-hero-primary">
                    Start Your Health Journey <span>→</span>
                  </Link>
                  <Link to="/login" className="landing-btn-hero-secondary">
                    Sign In to Account
                  </Link>
                </>
              )}
            </div>

            {/* Feature Pills */}
            <div className="hero-feature-tags">
              <div className="hero-tag-item">
                <span className="tag-check">✓</span>
                <span>Random Forest AI Classifier</span>
              </div>
              <div className="hero-tag-item">
                <span className="tag-check">✓</span>
                <span>Lab Biomarker Calibration</span>
              </div>
              <div className="hero-tag-item">
                <span className="tag-check">✓</span>
                <span>Diet-Safe 7-Day Meal Planner</span>
              </div>
            </div>
          </div>

          {/* Hero Visual Preview Card */}
          <div className="landing-hero-visual">
            <div className="hero-glass-card">
              <div className="glass-card-header">
                <div className="glass-avatar-icon">🌿</div>
                <div>
                  <h4 className="glass-header-title">Nutritional Assessment Snapshot</h4>
                  <span className="glass-header-sub">MultiOutput Random Forest Engine</span>
                </div>
                <span className="glass-score-pill">94.2% AI Confidence</span>
              </div>

              <div className="glass-metrics-grid">
                <div className="glass-metric-box">
                  <span className="metric-box-label">Wellness Score</span>
                  <span className="metric-box-val high">62.9%</span>
                  <span className="metric-box-sub">Good baseline</span>
                </div>
                <div className="glass-metric-box">
                  <span className="metric-box-label">Nutrients Evaluated</span>
                  <span className="metric-box-val">10 / 10</span>
                  <span className="metric-box-sub">Key biomarkers</span>
                </div>
              </div>

              {/* Sample Risk Bars */}
              <div className="glass-risk-sample-list">
                <div className="glass-sample-item">
                  <div className="sample-item-top">
                    <span className="sample-name">Iron</span>
                    <span className="sample-badge low">17% LOW</span>
                  </div>
                  <div className="sample-track">
                    <div className="sample-fill low" style={{ width: "17%" }}></div>
                  </div>
                </div>

                <div className="glass-sample-item">
                  <div className="sample-item-top">
                    <span className="sample-name">Calcium</span>
                    <span className="sample-badge high">95% HIGH RISK</span>
                  </div>
                  <div className="sample-track">
                    <div className="sample-fill high" style={{ width: "95%" }}></div>
                  </div>
                </div>

                <div className="glass-sample-item">
                  <div className="sample-item-top">
                    <span className="sample-name">Vitamin D</span>
                    <span className="sample-badge moderate">43% MODERATE</span>
                  </div>
                  <div className="sample-track">
                    <div className="sample-fill moderate" style={{ width: "43%" }}></div>
                  </div>
                </div>
              </div>

              <div className="glass-rec-preview">
                <span className="rec-preview-icon">🥑</span>
                <span>Top Match: <strong>Sesame seeds (til)</strong> · Ca 975mg per 100g</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Core Features Grid ── */}
      <section id="features" className="landing-features-section">
        <div className="section-container">
          <div className="section-title-wrap">
            <span className="section-badge">Core Capabilities</span>
            <h2 className="section-title">Engineered for Precision Nutrition</h2>
            <p className="section-subtitle">
              NutriSense combines clinical dietary records, laboratory values, and rule-based recommendation logic into an easy-to-use platform.
            </p>
          </div>

          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon-bubble emerald">📝</div>
              <h3 className="feature-card-title">Interactive Food Diary</h3>
              <p className="feature-card-text">
                Log daily meals across Breakfast, Lunch, Snack, and Dinner. Computes exact calories, macronutrients, and vitamins in real-time.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-bubble teal">🤖</div>
              <h3 className="feature-card-title">AI Deficiency Detection</h3>
              <p className="feature-card-text">
                MultiOutput Random Forest model evaluates 13 biomarker inputs to compute deficiency risk probabilities across 10 vital nutrients.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-bubble mint">🔬</div>
              <h3 className="feature-card-title">Biomarker Lab Integration</h3>
              <p className="feature-card-text">
                Calibrate predictions with your lab reports—including Hemoglobin, Ferritin, Serum Vitamin D, Vitamin B12, and Calcium.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-bubble gold">🥑</div>
              <h3 className="feature-card-title">Targeted Food Recommender</h3>
              <p className="feature-card-text">
                Rule-based engine suggests top nutrient-dense foods prioritized by authentic Indian & curated sources for your high-risk deficiencies.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-bubble forest">🍽️</div>
              <h3 className="feature-card-title">7-Day Varied Meal Planner</h3>
              <p className="feature-card-text">
                Generates a complete Sunday-to-Saturday schedule with 4 meals/day and 2 unique foods/meal—ensuring 56 non-repeating foods each week.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-bubble sage">📈</div>
              <h3 className="feature-card-title">Progress & Risk Tracking</h3>
              <p className="feature-card-text">
                Track your wellness score trajectory and deficiency reductions over weekly assessment milestones.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── How It Works Step Section ── */}
      <section id="how-it-works" className="landing-steps-section">
        <div className="section-container">
          <div className="section-title-wrap">
            <span className="section-badge">Simple Workflow</span>
            <h2 className="section-title">How NutriSense Works</h2>
            <p className="section-subtitle">
              Follow four straightforward steps from daily meal logging to actionable nutritional planning.
            </p>
          </div>

          <div className="steps-flow-grid">
            <div className="step-flow-card">
              <div className="step-number-circle">01</div>
              <h4 className="step-card-title">Log Meals</h4>
              <p className="step-card-desc">
                Record your daily breakfast, lunch, dinner, and snacks in your Food Diary.
              </p>
            </div>

            <div className="step-flow-card">
              <div className="step-number-circle">02</div>
              <h4 className="step-card-title">Add Lab Data</h4>
              <p className="step-card-desc">
                Optionally enter your latest blood test biomarkers for enhanced precision.
              </p>
            </div>

            <div className="step-flow-card">
              <div className="step-number-circle">03</div>
              <h4 className="step-card-title">Run AI Assessment</h4>
              <p className="step-card-desc">
                Let the Random Forest classifier evaluate your 10 vital nutrient risks.
              </p>
            </div>

            <div className="step-flow-card">
              <div className="step-number-circle">04</div>
              <h4 className="step-card-title">Enjoy Your Meal Plan</h4>
              <p className="step-card-desc">
                Receive customized, diet-compliant meal plans with diverse, whole foods.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Evaluated Nutrients Section ── */}
      <section id="nutrients" className="landing-nutrients-section">
        <div className="section-container">
          <div className="section-title-wrap">
            <span className="section-badge">Comprehensive Coverage</span>
            <h2 className="section-title">10 Evaluated Nutrients</h2>
            <p className="section-subtitle">
              NutriSense assesses essential micronutrients and macronutrients to deliver a complete nutritional picture.
            </p>
          </div>

          <div className="nutrient-chips-container">
            {[
              { name: "Iron (Fe)", desc: "Energy & Oxygen Transport" },
              { name: "Calcium (Ca)", desc: "Bone Density & Muscle Function" },
              { name: "Vitamin B12", desc: "Nerve Health & Red Blood Cells" },
              { name: "Vitamin D", desc: "Immune System & Calcium Absorption" },
              { name: "Protein", desc: "Muscle Repair & Enzyme Synthesis" },
              { name: "Folate", desc: "DNA Synthesis & Cell Division" },
              { name: "Vitamin A", desc: "Vision & Immune Defense" },
              { name: "Vitamin C", desc: "Antioxidant & Collagen Support" },
              { name: "Magnesium", desc: "Energy Production & Muscle Recovery" },
              { name: "Zinc", desc: "Immunity & Cellular Metabolism" },
            ].map((n) => (
              <div key={n.name} className="nutrient-chip-card">
                <span className="nutrient-chip-name">{n.name}</span>
                <span className="nutrient-chip-desc">{n.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Bottom Call To Action Banner ── */}
      <section className="landing-cta-banner-section">
        <div className="section-container">
          <div className="cta-banner-glass">
            <h2 className="cta-banner-title">
              Ready to Take Control of Your Nutrition?
            </h2>
            <p className="cta-banner-subtitle">
              Start logging your meals today to uncover deficiency risks and unlock personalized dietary guidance.
            </p>
            <div className="cta-banner-buttons">
              {isAuthenticated ? (
                <button
                  className="landing-btn-hero-primary"
                  onClick={() => navigate("/dashboard")}
                >
                  Enter Dashboard
                </button>
              ) : (
                <Link to="/signup" className="landing-btn-hero-primary">
                  Create Free Account
                </Link>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        <div className="section-container footer-content-wrap">
          <div className="footer-brand-side">
            <div className="landing-brand">
              <span className="brand-leaf-icon">🌱</span>
              <span className="brand-logo-text">NutriSense</span>
            </div>
            <p className="footer-tagline">
              AI-based nutritional assessment and personalized meal planning system.
            </p>
          </div>

          <div className="footer-links-side">
            <div className="footer-links-col">
              <h5>Navigation</h5>
              <Link to="/login">Sign In</Link>
              <Link to="/signup">Register</Link>
              <Link to="/dashboard">Dashboard</Link>
            </div>
            <div className="footer-links-col">
              <h5>Features</h5>
              <a href="#features">AI Assessment</a>
              <a href="#how-it-works">How It Works</a>
              <a href="#nutrients">10 Nutrients</a>
            </div>
          </div>
        </div>
        <div className="footer-bottom-bar">
          <p>© 2026 NutriSense AI. Educational and nutritional decision support demonstration.</p>
        </div>
      </footer>
    </div>
  );
}
