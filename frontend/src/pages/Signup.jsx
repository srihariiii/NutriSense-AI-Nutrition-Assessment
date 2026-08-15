import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { saveAuth, signup } from "../api/api";

export default function Signup() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    if (form.password !== form.confirm_password) { setError("Passwords do not match"); return; }
    if (form.password.length < 6) { setError("Password must be at least 6 characters"); return; }
    if (!/[a-zA-Z]/.test(form.password) || !/\d/.test(form.password)) {
      setError("Password must contain at least one letter and one number"); return;
    }
    setLoading(true);
    try {
      const data = await signup(form);
      saveAuth(data.access_token, data.user);
      navigate("/health-profile");
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
          <h1 className="auth-hero-title">Start Your Nutrition Journey</h1>
          <p className="auth-hero-subtitle">
            Understand your body's needs with AI-powered nutritional assessment and personalized meal planning.
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
            <button className="auth-tab" onClick={() => navigate("/login")}>Sign In</button>
            <button className="auth-tab active">Register</button>
          </div>

          <h2 className="auth-form-title">Create your account</h2>
          <p className="auth-form-subtitle">Register to calculate your requirements and track foods.</p>

          {error && <div className="error-msg">{error}</div>}

          <form onSubmit={handleSubmit}>
            <div className="row-2">
              <div className="form-group">
                <label htmlFor="first_name">First name</label>
                <input id="first_name" name="first_name" type="text" placeholder="Enter first name" value={form.first_name} onChange={handleChange} required />
              </div>
              <div className="form-group">
                <label htmlFor="last_name">Last name</label>
                <input id="last_name" name="last_name" type="text" placeholder="Enter last name" value={form.last_name} onChange={handleChange} required />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="email">Email address</label>
              <input id="email" name="email" type="email" placeholder="you@example.com" value={form.email} onChange={handleChange} required />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input id="password" name="password" type="password" placeholder="Create a password" value={form.password} onChange={handleChange} required />
              <p className="hint">At least 6 characters with one letter and one number.</p>
            </div>

            <div className="form-group">
              <label htmlFor="confirm_password">Confirm password</label>
              <input id="confirm_password" name="confirm_password" type="password" placeholder="Confirm your password" value={form.confirm_password} onChange={handleChange} required />
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "Creating account..." : "Create account"}
            </button>
          </form>

          <p className="auth-switch">
            Already have an account? <span onClick={() => navigate("/login")}>Sign in</span>
          </p>
        </div>
      </div>
    </div>
  );
}
