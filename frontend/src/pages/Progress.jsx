import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { clearAuth, fetchProfile, getToken, getUser, fetchProgress } from "../api/api";

const DEFAULT_HISTORY = [
  { id: 1, week_label: "W1", wellness_score: 60.7, avg_risk: 39.3, top_risks_summary: "Iron 14% · Vit D 65%" },
  { id: 2, week_label: "W2", wellness_score: 60.7, avg_risk: 39.3, top_risks_summary: "Iron 14% · Vit D 65%" },
  { id: 3, week_label: "W3", wellness_score: 60.7, avg_risk: 39.3, top_risks_summary: "Iron 14% · Vit D 65%" },
  { id: 4, week_label: "W4", wellness_score: 60.7, avg_risk: 39.3, top_risks_summary: "Iron 14% · Vit D 65%" },
  { id: 5, week_label: "W5", wellness_score: 60.7, avg_risk: 39.3, top_risks_summary: "Iron 14% · Vit D 65%" },
  { id: 6, week_label: "W6", wellness_score: 60.7, avg_risk: 39.3, top_risks_summary: "Iron 14% · Vit D 65%" },
];

export default function Progress() {
  const navigate = useNavigate();
  const [user, setUser] = useState(getUser());
  const [loading, setLoading] = useState(true);
  const [historyList, setHistoryList] = useState(DEFAULT_HISTORY);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      navigate("/login");
      return;
    }

    fetchProfile()
      .then((userData) => {
        if (userData) setUser(userData);
      })
      .catch(() => null);

    fetchProgress()
      .then((res) => {
        if (res && Array.isArray(res.history) && res.history.length > 0) {
          if (res.history.length >= 6) {
            setHistoryList(res.history.slice(-6));
          } else {
            const list = [...res.history];
            const lastItem = list[list.length - 1];
            while (list.length < 6) {
              const nextIdx = list.length + 1;
              list.push({
                id: nextIdx,
                week_label: "W" + nextIdx,
                wellness_score: lastItem.wellness_score,
                avg_risk: lastItem.avg_risk,
                top_risks_summary: lastItem.top_risks_summary,
              });
            }
            setHistoryList(list);
          }
        }
      })
      .catch((err) => {
        console.error("Failed to load progress:", err);
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

      {/* Main Content Area */}
      <main className="diary-main progress-page-bg">
        <div className="progress-header-container">
          <h1 className="progress-title">Progress</h1>
        </div>

        <div className="progress-two-col">
          {/* Left: Average Risk Bar Chart */}
          <div className="progress-card">
            <h3 className="progress-card-title">Average risk (lower is better)</h3>

            <div className="progress-chart-wrap">
              <div className="progress-bars-row">
                {historyList.map((item, idx) => {
                  const riskVal = typeof item.avg_risk === "number" ? item.avg_risk : 39.3;
                  const barHeight = Math.max(30, Math.min(100, Math.round((riskVal / 70) * 100)));

                  return (
                    <div key={item.week_label || idx} className="progress-bar-col">
                      <div
                        className="progress-bar-fill"
                        style={{ height: barHeight + "%" }}
                        title={item.week_label + ": " + riskVal + "% Risk (Score: " + item.wellness_score + "%)"}
                      ></div>
                      <span className="progress-bar-label">{item.week_label}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right: History Log */}
          <div className="progress-card">
            <h3 className="progress-card-title">History</h3>

            <div className="history-list">
              {historyList.map((item, idx) => (
                <div key={item.id || idx} className="history-item">
                  <div className="history-left">
                    <span>{item.week_label}</span>
                    <span className="dot-sep" style={{ margin: "0 0.2rem" }}>·</span>
                    <span className="history-score">score {item.wellness_score}%</span>
                  </div>
                  <div className="history-right">
                    <span>{item.top_risks_summary}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
