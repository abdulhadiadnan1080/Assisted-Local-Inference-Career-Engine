import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { AliceProvider } from "./lib/useAlice";
import SiteLayout from "./components/SiteLayout";
import WorkspaceLayout from "./components/WorkspaceLayout";
import Landing from "./pages/Landing";
import Product from "./pages/Product";
import About from "./pages/About";
import Setup from "./pages/Setup";
import Automate from "./pages/Automate";
import Manual from "./pages/Manual";
import Briefing from "./pages/Briefing";
import Letters from "./pages/Letters";
import Intake from "./pages/Intake";
import Lab from "./pages/Lab";
import Database from "./pages/Database";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <AliceProvider>
        <ScrollToTop />
        <Routes>
          <Route element={<SiteLayout />}>
            <Route path="/" element={<Landing />} />
            <Route path="/product" element={<Product />} />
            <Route path="/about" element={<About />} />
            <Route path="/setup" element={<Setup />} />
            <Route path="/automate" element={<Automate />} />
            <Route path="/manual" element={<Manual />} />
            <Route path="/lab" element={<Lab />} />
          </Route>
          <Route element={<WorkspaceLayout />}>
            <Route path="/app" element={<Navigate to="/app/briefing" replace />} />
            <Route path="/app/briefing" element={<Briefing />} />
            <Route path="/app/letters" element={<Letters />} />
            <Route path="/app/intake" element={<Intake />} />
            <Route path="/app/database" element={<Database />} />
            <Route path="/database" element={<Navigate to="/app/database" replace />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AliceProvider>
    </BrowserRouter>
  );
}
