import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { clearAuth, fetchProfile, getToken, getUser } from "../api/api";

export default function Profile() {
  const navigate = useNavigate();
  const [user, setUser] = useState(getUser());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      navigate("/login");
      return;
    }

    fetchProfile()
      .then((data) => setUser(data))
      .catch(() => {
        clearAuth();
        navigate("/login");
      })
      .finally(() => setLoading(false));
  }, [navigate]);

  function handleLogout() {
    clearAuth();
    navigate("/login");
  }

  if (loading) {
    return (
      <div className="page profile-page">
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="page profile-page">
      <div className="profile-card">
        <div className="brand" style={{ justifyContent: "center", marginBottom: "1.5rem" }}>
          NutriSense
          <span className="brand-badge">AI</span>
        </div>

        <div className="profile-icon">🥗</div>

        <h1 className="profile-name">
          {user?.first_name} {user?.last_name}
        </h1>
        <p className="profile-email">{user?.email}</p>

        <p className="ai-tagline">
          Your AI nutrition dashboard will appear here — deficiency detection,
          meal planning, and personalized insights coming soon.
        </p>

        <button type="button" className="btn btn-logout" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </div>
  );
}
