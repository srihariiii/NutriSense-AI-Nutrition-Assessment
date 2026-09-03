import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import { clearAuth, getUser, searchFoods, fetchDiaryEntries, addDiaryEntry, deleteDiaryEntry } from "../api/api";

export default function FoodDiary() {
  const navigate = useNavigate();
  const user = getUser();

  const [date, setDate] = useState("");
  const [mealType, setMealType] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [selectedFood, setSelectedFood] = useState(null);
  const [portion, setPortion] = useState("");
  const [entries, setEntries] = useState([]);
  const [showCalendar, setShowCalendar] = useState(false);
  const [calendarMonth, setCalendarMonth] = useState(new Date());
  const [statusMsg, setStatusMsg] = useState("");

  const searchTimeout = useRef(null);
  const calendarRef = useRef(null);

  // Close calendar on outside click
  useEffect(() => {
    const handler = (e) => {
      if (calendarRef.current && !calendarRef.current.contains(e.target)) {
        setShowCalendar(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    if (!user) {
      navigate("/login");
      return;
    }
    if (date) loadEntries(date);
  }, [date, navigate]);

  const loadEntries = async (d) => {
    try {
      const data = await fetchDiaryEntries(d);
      setEntries(data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSearchChange = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    if (!query) {
      setSearchResults([]);
      setSelectedFood(null);
      return;
    }
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(async () => {
      try {
        const results = await searchFoods(query);
        setSearchResults(results);
      } catch (err) {
        console.error(err);
      }
    }, 300);
  };

  const selectFood = (food) => {
    setSelectedFood({ id: food.id, name: food.name });
    setSearchQuery(food.name);
    setSearchResults([]);
  };

  const handleAddEntry = async () => {
    if (!date) { setStatusMsg("Please select a date first."); return; }
    if (!mealType) { setStatusMsg("Please select a meal type."); return; }
    if (!selectedFood) { setStatusMsg("Please search and select a food."); return; }
    if (!portion) { setStatusMsg("Please enter portion in grams."); return; }
    try {
      await addDiaryEntry({
        date,
        meal_type: mealType,
        food_item_id: selectedFood.id,
        food_name: selectedFood.name,
        portion_grams: Number(portion),
      });
      setSelectedFood(null);
      setSearchQuery("");
      setPortion("");
      setStatusMsg("Meal logged successfully!");
      setTimeout(() => setStatusMsg(""), 2500);
      loadEntries(date);
    } catch (err) {
      console.error(err);
      setStatusMsg("Failed to log meal.");
    }
  };

  const handleRemove = async (id) => {
    try {
      await deleteDiaryEntry(id);
      loadEntries(date);
    } catch (err) {
      console.error(err);
    }
  };

  const handleLogout = () => {
    clearAuth();
    navigate("/login");
  };

  // Calendar helpers
  const getDaysInMonth = (year, month) => new Date(year, month + 1, 0).getDate();
  const getFirstDayOfMonth = (year, month) => new Date(year, month, 1).getDay();

  const renderCalendar = () => {
    const year = calendarMonth.getFullYear();
    const month = calendarMonth.getMonth();
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);
    const today = new Date();
    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

    const days = [];
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`e-${i}`} className="calendar-day empty"></div>);
    }
    for (let i = 1; i <= daysInMonth; i++) {
      const d = new Date(year, month, i);
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, "0");
      const day = String(d.getDate()).padStart(2, "0");
      const dateStr = `${y}-${m}-${day}`;
      const isSelected = date === dateStr;
      const isToday = dateStr === todayStr;
      days.push(
        <div
          key={i}
          className={`calendar-day${isSelected ? " selected" : ""}${isToday && !isSelected ? " today" : ""}`}
          onClick={() => { setDate(dateStr); setShowCalendar(false); }}
        >
          {i}
        </div>
      );
    }
    return days;
  };

  const prevMonth = () => setCalendarMonth(new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() - 1, 1));
  const nextMonth = () => setCalendarMonth(new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() + 1, 1));

  // Format DD/MM/YYYY for display
  const formattedDate = date
    ? (() => { const [y, m, d] = date.split("-"); return `${d}/${m}/${y}`; })()
    : "";

  // Format for entries header
  const entriesHeader = date
    ? (() => {
        const [y, m, d] = date.split("-");
        const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
        return `${parseInt(d)} ${months[parseInt(m) - 1]} ${y}`;
      })()
    : "—";

  return (
    <div className="diary-layout">
      {/* Sidebar with Desktop Sticky & Mobile Drawer */}
      <Sidebar user={user} onLogout={handleLogout} />

      {/* ── Main content ── */}
      <main className="diary-main diary-main-with-bg">
        <div className="diary-page-header">
          <h1>Food diary</h1>
          <p>Search foods and log portions — nutrients computed automatically.</p>
        </div>

        <div className="diary-content">
          {/* Left: Log meal form */}
          <div className="diary-form-panel">
            <h2>Log meal</h2>
            {statusMsg && (
              <div className={`diary-status ${statusMsg.includes("success") ? "success" : ""}`}>
                {statusMsg}
              </div>
            )}

            {/* Date */}
            <div className="form-group" ref={calendarRef}>
              <label>Date</label>
              <div className="date-input-wrap">
                <input
                  type="text"
                  value={formattedDate}
                  placeholder="Select a date"
                  readOnly
                  onClick={() => setShowCalendar(!showCalendar)}
                />
                <button className="calendar-btn" type="button" onClick={() => setShowCalendar(!showCalendar)}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                </button>
                {showCalendar && (
                  <div className="calendar-popup">
                    <div className="calendar-header">
                      <button type="button" onClick={prevMonth}>&lsaquo;</button>
                      <span>{calendarMonth.toLocaleString("default", { month: "long", year: "numeric" })}</span>
                      <button type="button" onClick={nextMonth}>&rsaquo;</button>
                    </div>
                    <div className="calendar-grid">
                      {["Su","Mo","Tu","We","Th","Fr","Sa"].map(d => (
                        <div key={d} className="calendar-day-header">{d}</div>
                      ))}
                      {renderCalendar()}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Meal */}
            <div className="form-group">
              <label>Meal</label>
              <select value={mealType} onChange={(e) => setMealType(e.target.value)}>
                <option value="" disabled>Select meal type</option>
                <option value="breakfast">Breakfast</option>
                <option value="lunch">Lunch</option>
                <option value="dinner">Dinner</option>
                <option value="snack">Snack</option>
              </select>
            </div>

            {/* Search food */}
            <div className="form-group food-search-wrapper">
              <label>Search food</label>
              <input
                type="text"
                placeholder="Type to search — dal, palak, chawal, paneer..."
                value={searchQuery}
                onChange={handleSearchChange}
              />
              {searchResults.length > 0 && (
                <div className="food-search-dropdown">
                  {searchResults.map((result) => (
                    <div key={result.id} className="food-search-item" onClick={() => selectFood(result)}>
                      <span className="search-food-name">{result.name}</span>
                      <span className="search-food-meta">{Math.round(result.energy_kcal)} kcal · Fe {result.iron_mg.toFixed(1)}mg</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Portion */}
            <div className="form-group">
              <label>Portion (grams)</label>
              <input
                type="number"
                placeholder="Enter portion in grams"
                value={portion}
                onChange={(e) => setPortion(e.target.value)}
                min="1"
              />
            </div>

            <button className="btn btn-primary diary-add-btn" onClick={handleAddEntry}>
              Add to diary
            </button>
          </div>

          {/* Right: Entries panel — matching user screenshot */}
          <div className="diary-entries-panel">
            <h2>Entries on {date || "—"}</h2>
            <div className="entries-list">
              {!date ? (
                <div className="entries-empty">
                  <p>Select a date to see your entries.</p>
                </div>
              ) : entries.length === 0 ? (
                <div className="entries-empty">
                  <p>No entries logged for this date yet.</p>
                  <span>Use the form to add your first meal!</span>
                </div>
              ) : (
                entries.map((entry) => (
                  <div key={entry.id} className="diary-entry-card">
                    <div className="diary-entry-card-header">
                      <span className="entry-meal-title">
                        {entry.meal_type ? entry.meal_type.charAt(0).toUpperCase() + entry.meal_type.slice(1) : "Meal"}
                      </span>
                    </div>
                    <div className="diary-entry-card-divider">&mdash;</div>
                    <div className="diary-entry-card-body">
                      <span className="entry-food-name">{entry.food_name} ({entry.portion_grams}g)</span>
                      <div className="entry-card-actions">
                        <span className="entry-stats">
                          {Math.round(entry.energy_kcal || 0)} kcal &middot; Fe {(entry.iron_mg || 0).toFixed(3)}mg
                        </span>
                        <button className="diary-entry-remove" onClick={() => handleRemove(entry.id)}>
                          Remove
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

