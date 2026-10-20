import { Link, NavLink, Outlet } from "react-router-dom";
import { useAlice } from "../lib/useAlice";

const navClass = ({ isActive }: { isActive: boolean }) => (isActive ? "on" : undefined);

export function Logo() {
  return (
    <Link className="logo" to="/" aria-label="ALICE by Hadi Adnan">
      <span className="word">ALICE</span>
      <span className="by">by Hadi Adnan</span>
    </Link>
  );
}

export function SiteHeader() {
  const { online, checked, state } = useAlice();
  const status = !checked ? "" : online ? (state?.running ? "running" : "on") : "off";

  return (
    <header className="site-header">
      <div className="wrap bar">
        <Logo />
        <nav className="site-nav">
          <NavLink to="/" className={navClass} end>
            Home
          </NavLink>
          <NavLink to="/product" className={navClass}>
            Product
          </NavLink>
          <NavLink to="/automate" className={navClass}>
            Automate
          </NavLink>
          <NavLink to="/manual" className={navClass}>
            Manual run
          </NavLink>
          <NavLink to="/lab" className={navClass}>
            Lab
          </NavLink>
          <NavLink to="/app/database" className={navClass}>
            Database
          </NavLink>
          <NavLink to="/about" className={navClass}>
            About
          </NavLink>
        </nav>
        <div className="header-cta">
          {status ? (
            <span className={`dot-status ${status}`} title={online ? "Engine reachable on 8471" : "Engine offline"}>
              <i />
              {online ? (state?.running ? "Running" : "Engine up") : "Offline"}
            </span>
          ) : null}
          <Link className="btn btn-quiet btn-sm" to="/setup">
            Setup
          </Link>
          <Link className="btn btn-primary btn-sm" to="/app/briefing">
            Open workspace
          </Link>
        </div>
      </div>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="wrap">
        <div className="footer-grid">
          <div>
            <Logo />
            <p className="small" style={{ marginTop: 12, maxWidth: "26em" }}>
              Assisted Local Inference Career Engine. Scored and papered on your own machine. Nothing is sent without your click.
            </p>
          </div>
          <div>
            <h5>Workspace</h5>
            <Link to="/app/briefing">Briefing</Link>
            <Link to="/app/letters">Letters</Link>
            <Link to="/app/intake">Intake</Link>
            <Link to="/app/database">Database</Link>
          </div>
          <div>
            <h5>Operate</h5>
            <Link to="/setup">Setup</Link>
            <Link to="/lab">Lab</Link>
            <Link to="/automate">Automate</Link>
            <Link to="/manual">Manual run</Link>
          </div>
          <div>
            <h5>Company</h5>
            <Link to="/">Home</Link>
            <Link to="/about">About</Link>
            <Link to="/product">How it works</Link>
            <a href="http://127.0.0.1:8471/docs">API</a>
          </div>
        </div>
        <div className="footer-bottom">
          <span>© {new Date().getFullYear()} Alice · built by Hadi Adnan</span>
          <span>Local inference · $0 per run · no cloud model calls</span>
        </div>
      </div>
    </footer>
  );
}

export default function SiteLayout() {
  return (
    <>
      <SiteHeader />
      <main>
        <Outlet />
      </main>
      <SiteFooter />
    </>
  );
}
