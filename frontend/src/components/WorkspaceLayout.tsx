import { NavLink, Outlet } from "react-router-dom";
import { SiteHeader } from "./SiteLayout";
import { useAlice, useJobs } from "../lib/useAlice";

const navClass = ({ isActive }: { isActive: boolean }) => (isActive ? "on" : undefined);

export default function WorkspaceLayout() {
  const { state, online } = useAlice();
  const briefing = useJobs("briefing");
  const intake = useJobs("intake");
  const drafts = briefing.jobs.filter((j) => j.letter.body).length;

  return (
    <>
      <SiteHeader />
      <div className="ws">
        <aside className="ws-rail">
          <h6>Today</h6>
          <nav>
            <NavLink to="/app/briefing" className={navClass}>
              Briefing <span className="count">{briefing.jobs.length}</span>
            </NavLink>
            <NavLink to="/app/letters" className={navClass}>
              Letters <span className="count">{drafts}</span>
            </NavLink>
            <NavLink to="/app/intake" className={navClass}>
              Intake <span className="count">{intake.jobs.length}</span>
            </NavLink>
            <NavLink to="/app/database" className={navClass}>
              Database
            </NavLink>
          </nav>
          <h6>Control</h6>
          <nav>
            <NavLink to="/automate" className={navClass}>
              Automate
            </NavLink>
            <NavLink to="/manual" className={navClass}>
              Manual run
            </NavLink>
            <NavLink to="/lab" className={navClass}>
              Lab
            </NavLink>
          </nav>
          <p className="rail-note">
            {!online
              ? "Backend offline. The workspace is showing the sample deck so the shape of a day is still readable."
              : briefing.source === "sample"
                ? "Connected, but nothing has been released yet. Seed a deck or turn on live crawl."
                : state?.liveCrawl
                  ? `Live crawl is on. ${state.jdBudget} description fetches left today.`
                  : "Live crawl is off. These are the jobs already in SQLite."}
          </p>
        </aside>
        <main className="ws-main">
          <Outlet />
        </main>
      </div>
    </>
  );
}
