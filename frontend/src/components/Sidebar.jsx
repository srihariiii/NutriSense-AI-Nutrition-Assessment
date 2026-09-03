import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";

export default function Sidebar({ user, onLogout }) {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  // Auto-close drawer on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  // Prevent background scrolling when mobile menu is open
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  const links = [
    { to: "/dashboard", label: "Dashboard", icon: "📊" },
    { to: "/food-diary", label: "Food diary", icon: "📝" },
    { to: "/lab-results", label: "Lab results", icon: "🔬" },
    { to: "/assessment", label: "Assessment", icon: "📋" },
    { to: "/meal-plan", label: "Meal plan", icon: "🍽️" },
    { to: "/progress", label: "Progress", icon: "📈" },
    { to: "/profile", label: "Profile", icon: "⚙️" },
  ];

  const currentLink = links.find((l) => l.to === location.pathname);
  const pageTitle = currentLink ? currentLink.label : "NutriSense";

  return (
    <>
      {/* ── Mobile Top Header Bar (Visible on mobile only) ── */}
      <header className="mobile-top-bar">
        <button
          type="button"
          className="mobile-hamburger-btn"
          onClick={() => setMobileOpen(true)}
          aria-label="Open Navigation Menu"
        >
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
          <span className="hamburger-line"></span>
        </button>

        <div className="mobile-top-brand">
          <span className="mobile-brand-icon">🌱</span>
          <span className="mobile-brand-text">NutriSense</span>
        </div>

        <div className="mobile-top-page-badge">
          {pageTitle}
        </div>
      </header>

      {/* ── Mobile Backdrop Overlay ── */}
      <div
        className={`sidebar-backdrop ${mobileOpen ? "open" : ""}`}
        onClick={() => setMobileOpen(false)}
        aria-hidden="true"
      />

      {/* ── Sidebar (Desktop Sticky + Mobile Slide Drawer) ── */}
      <aside className={`diary-sidebar ${mobileOpen ? "mobile-drawer-open" : ""}`}>
        <div className="sidebar-header-row">
          <div className="diary-brand">
            <span className="brand-leaf-icon" style={{ fontSize: "1.4rem" }}>🌱</span>
            <span>NutriSense</span>
          </div>
          <button
            type="button"
            className="sidebar-close-btn"
            onClick={() => setMobileOpen(false)}
            aria-label="Close Navigation Menu"
          >
            ✕
          </button>
        </div>

        <div className="sidebar-user">
          {user?.first_name ? `${user.first_name} ${user.last_name || ""}` : user?.email || "User"}
        </div>

        <nav className="sidebar-nav">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={location.pathname === l.to ? "active" : ""}
              onClick={() => setMobileOpen(false)}
            >
              <span className="nav-icon">{l.icon}</span> {l.label}
            </Link>
          ))}
        </nav>

        <button
          className="sidebar-logout"
          onClick={() => {
            setMobileOpen(false);
            if (onLogout) onLogout();
          }}
        >
          Sign out
        </button>
      </aside>
    </>
  );
}
