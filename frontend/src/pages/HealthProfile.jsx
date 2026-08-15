import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  clearAuth,
  fetchHealthProfile,
  getToken,
  saveHealthProfile,
} from "../api/api";

const SEX_OPTIONS = ["Female", "Male"];

const ACTIVITY_LEVELS = [
  "Sedentary",
  "Lightly active",
  "Moderately active",
  "Very active",
  "Extremely active",
];

// Health goal is now a free-text input field

const DIETARY_OPTIONS = [
  "Vegetarian",
  "Vegan",
  "Gluten-free",
  "Dairy-free",
  "Nut allergy",
  "None",
];

const INITIAL_FORM = {
  age: "",
  sex: "",
  height_cm: "",
  weight_kg: "",
  activity_level: "",
  health_goal: "",
  dietary_restrictions: [],
};

export default function HealthProfile() {
  const navigate = useNavigate();
  const [form, setForm] = useState(INITIAL_FORM);
  const [errors, setErrors] = useState({});
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      navigate("/login");
      return;
    }

    fetchHealthProfile()
      .then((data) => {
        setForm({
          age: String(data.age),
          sex: data.sex,
          height_cm: String(data.height_cm),
          weight_kg: String(data.weight_kg),
          activity_level: data.activity_level,
          health_goal: data.health_goal,
          dietary_restrictions: data.dietary_restrictions,
        });
      })
      .catch((err) => {
        if (err.message.includes("Not authenticated") || err.message.includes("Invalid")) {
          clearAuth();
          navigate("/login");
        }
      })
      .finally(() => setCheckingAuth(false));
  }, [navigate]);

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: "" });
  }

  function toggleRestriction(option) {
    setErrors({ ...errors, dietary_restrictions: "" });

    if (option === "None") {
      setForm({ ...form, dietary_restrictions: ["None"] });
      return;
    }

    const withoutNone = form.dietary_restrictions.filter((r) => r !== "None");
    const updated = withoutNone.includes(option)
      ? withoutNone.filter((r) => r !== option)
      : [...withoutNone, option];

    setForm({ ...form, dietary_restrictions: updated });
  }

  function validate() {
    const nextErrors = {};

    if (!form.age) {
      nextErrors.age = "Please enter your age.";
    } else {
      const age = Number(form.age);
      if (age < 1 || age > 120) nextErrors.age = "Please enter a valid age (1–120).";
    }

    if (!form.sex) nextErrors.sex = "Please select your sex.";

    if (!form.height_cm) {
      nextErrors.height_cm = "Please enter your height.";
    } else if (Number(form.height_cm) <= 0) {
      nextErrors.height_cm = "Please enter a valid height.";
    }

    if (!form.weight_kg) {
      nextErrors.weight_kg = "Please enter your weight.";
    } else if (Number(form.weight_kg) <= 0) {
      nextErrors.weight_kg = "Please enter a valid weight.";
    }

    if (!form.activity_level) {
      nextErrors.activity_level = "Please select your activity level.";
    }

    if (!form.health_goal) {
      nextErrors.health_goal = "Please enter your health goal.";
    }

    if (form.dietary_restrictions.length === 0) {
      nextErrors.dietary_restrictions = "Please select at least one option.";
    }

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (!validate()) return;

    setLoading(true);

    try {
      await saveHealthProfile({
        age: Number(form.age),
        sex: form.sex,
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        activity_level: form.activity_level,
        health_goal: form.health_goal,
        dietary_restrictions: form.dietary_restrictions,
      });
      navigate("/food-diary");
    } catch (err) {
      if (
        err.message.includes("Cannot connect") ||
        err.message.includes("backend is running")
      ) {
        setError(
          "Unable to save your profile. Please make sure the backend is running."
        );
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }

  if (checkingAuth) {
    return (
      <div className="health-page">
        <p className="loading-text">Loading...</p>
      </div>
    );
  }

  return (
    <div className="health-page">
      <img src="/images/leaf.svg" alt="" className="health-deco health-deco-left" />
      <img src="/images/fruits.svg" alt="" className="health-deco health-deco-right" />

      <div className="health-container">
        <div className="health-header">
          <div className="brand brand-center">
            NutriSense
            <span className="brand-badge">AI</span>
          </div>
          <h1 className="title title-center">Your health profile</h1>
          <p className="subtitle subtitle-center">
            We use this information to personalize RDA targets and meal recommendations.
          </p>
        </div>

        <div className="health-hero-img">
          <img src="/images/nutrition-hero.png" alt="Healthy foods" />
        </div>

        <div className="health-card">
          {error && <div className="error-msg">{error}</div>}

          <form onSubmit={handleSubmit} className="health-form">
            <div className="row-2">
              <div className="form-group">
                <label htmlFor="age">Age</label>
                <input
                  id="age"
                  name="age"
                  type="number"
                  min="1"
                  max="120"
                  placeholder="Enter your age"
                  value={form.age}
                  onChange={handleChange}
                />
                {errors.age && <p className="field-error">{errors.age}</p>}
              </div>

              <div className="form-group">
                <label htmlFor="sex">Sex</label>
                <select id="sex" name="sex" value={form.sex} onChange={handleChange}>
                  <option value="">Select</option>
                  {SEX_OPTIONS.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
                {errors.sex && <p className="field-error">{errors.sex}</p>}
              </div>
            </div>

            <div className="row-2">
              <div className="form-group">
                <label htmlFor="height_cm">Height (cm)</label>
                <input
                  id="height_cm"
                  name="height_cm"
                  type="number"
                  min="1"
                  step="0.1"
                  placeholder="Enter your height"
                  value={form.height_cm}
                  onChange={handleChange}
                />
                {errors.height_cm && <p className="field-error">{errors.height_cm}</p>}
              </div>

              <div className="form-group">
                <label htmlFor="weight_kg">Weight (kg)</label>
                <input
                  id="weight_kg"
                  name="weight_kg"
                  type="number"
                  min="1"
                  step="0.1"
                  placeholder="Enter your weight"
                  value={form.weight_kg}
                  onChange={handleChange}
                />
                {errors.weight_kg && <p className="field-error">{errors.weight_kg}</p>}
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="activity_level">Activity level</label>
              <select
                id="activity_level"
                name="activity_level"
                value={form.activity_level}
                onChange={handleChange}
              >
                <option value="">Select activity level</option>
                {ACTIVITY_LEVELS.map((opt) => (
                  <option key={opt} value={opt}>
                    {opt}
                  </option>
                ))}
              </select>
              {errors.activity_level && (
                <p className="field-error">{errors.activity_level}</p>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="health_goal">Health goal</label>
              <input
                id="health_goal"
                name="health_goal"
                type="text"
                placeholder="Enter your health goal"
                value={form.health_goal}
                onChange={handleChange}
              />
              {errors.health_goal && <p className="field-error">{errors.health_goal}</p>}
            </div>

            <div className="form-group">
              <label>Dietary restrictions</label>
              <div className="chip-group">
                {DIETARY_OPTIONS.map((option) => (
                  <button
                    key={option}
                    type="button"
                    className={`chip ${
                      form.dietary_restrictions.includes(option) ? "chip-active" : ""
                    }`}
                    onClick={() => toggleRestriction(option)}
                  >
                    {option}
                  </button>
                ))}
              </div>
              {errors.dietary_restrictions && (
                <p className="field-error">{errors.dietary_restrictions}</p>
              )}
            </div>

            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? "Saving..." : "Save & continue"}
            </button>
          </form>
        </div>

        <img src="/images/salad.svg" alt="" className="health-deco-bottom" />
      </div>
    </div>
  );
}
