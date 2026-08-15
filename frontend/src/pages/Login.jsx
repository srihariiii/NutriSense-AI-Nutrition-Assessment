import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, saveAuth, navigateAfterAuth } from "../api/api";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login({ email, password });
      saveAuth(data.access_token, data.user);
      await navigateAfterAuth(navigate);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-layout">
      {/* Left branding panel */}
      <div className="auth-hero">
        <div className="auth-hero-overlay"></div>
        <div className="auth-hero-content">
          <div className="auth-hero-brand">
            <span className="auth-leaf">🍃</span> NutriSense AI
          </div>
          <h1 className="auth-hero-title">Your AI-Powered Nutrition Companion</h1>
          <p className="auth-hero-subtitle">
            Holistic nutritional assessment, personalized meal guidance &amp; food tracking — powered by intelligent analysis.
          </p>
          <div className="auth-hero-features">
            <div className="auth-feature"><span>✓</span> Track daily nutrition intake</div>
            <div className="auth-feature"><span>✓</span> Detect nutrient deficiencies</div>
            <div className="auth-feature"><span>✓</span> Personalized meal plans</div>
            <div className="auth-feature"><span>✓</span> 8,000+ food database</div>
          </div>
        </div>
      </div>

      {/* Right form panel */}
      <div className="auth-form-panel">
        <div className="auth-form-container">
          <div className="auth-tabs">
            <button className="auth-tab active">Sign In</button>
            <button className="auth-tab" onClick={() => navigate("/signup")}>Register</button>
          </div>

          <h2 className="auth-form-title">Welcome back</h2>
          <p className="auth-form-subtitle">Sign in to continue your nutrition journey.</p>

          {error && <div className="error-msg">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="email">Email address</label>
              <input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p className="auth-switch">
            Don't have an account? <span onClick={() => navigate("/signup")}>Create one</span>
          </p>
        </div>
      </div>
    </div>
  );
}
