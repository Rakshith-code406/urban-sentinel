import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";

const DEFAULT_LINKS = [
  { to: "/home", label: "Dashboard" },
  { to: "/report", label: "Report Issue" },
  { to: "/track", label: "Track Complaint" },
];

function Navbar({
  links = DEFAULT_LINKS,
  cta = null,
  subtitle = "Civic response and monitoring",
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 760) {
        setMenuOpen(false);
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  return (
    <header className="app-topbar">
      <div className="app-shell">
        <div className="app-topbar__inner">
          <NavLink to="/home" className="app-topbar__brand" onClick={() => setMenuOpen(false)}>
            <span className="app-topbar__mark" aria-hidden="true">
              US
            </span>
            <span className="app-topbar__brand-text">
              <strong>Urban Sentinel</strong>
              <span>{subtitle}</span>
            </span>
          </NavLink>

          <button
            type="button"
            className="app-topbar__toggle"
            aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((value) => !value)}
          >
            {menuOpen ? "Close" : "Menu"}
          </button>

          <nav className="app-topbar__nav" data-open={menuOpen}>
            <div className="app-topbar__links">
              {links.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  onClick={() => setMenuOpen(false)}
                  className={({ isActive }) =>
                    `app-topbar__link${isActive ? " app-topbar__link--active" : ""}`
                  }
                >
                  {link.label}
                </NavLink>
              ))}
            </div>
            {cta ? (
              <NavLink to={cta.to} className="app-topbar__cta" onClick={() => setMenuOpen(false)}>
                {cta.label}
              </NavLink>
            ) : null}
          </nav>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
