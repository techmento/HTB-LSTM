import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import Login from "./components/Login";
import InputPanel from "./components/InputPanel";
import SummaryCards from "./components/SummaryCards";
import FaultProbabilityChart from "./components/FaultProbabilityChart";
import PredictionsTable from "./components/PredictionsTable";
import AlertsPanel from "./components/AlertsPanel";
import OperationalCharts from "./components/OperationalCharts";
import DescriptiveStats from "./components/DescriptiveStats";
import CorrelationMatrix from "./components/CorrelationMatrix";
import FaultDistribution from "./components/FaultDistribution";
import ModelPerformance from "./components/ModelPerformance";
import ConfusionMatrix from "./components/ConfusionMatrix";
import Footer from "./components/Footer";
import {
  getDatasetStats,
  getModelPerformance,
  getHistory,
  saveHistory,
  isLoggedIn,
  logout as apiLogout,
} from "./api/api";

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(isLoggedIn());

  // Prediction results — seeded from saved history on login/mount so a page
  // refresh doesn't lose earlier work, then appended to as new predictions
  // come in (each new prediction is also persisted via saveHistory()).
  const [results, setResults] = useState([]);

  // Fetched once on mount — these don't depend on user input at all.
  const [datasetStats, setDatasetStats] = useState({ data: null, loading: true, error: null });
  const [modelPerformance, setModelPerformance] = useState({ data: null, loading: true, error: null });
  const [lastUpdated, setLastUpdated] = useState(null);

  // If any API call comes back 401 (session expired/invalid), api.js clears
  // the token and fires this event — fall back to the login screen.
  useEffect(() => {
    function handleAuthLogout() {
      setIsAuthenticated(false);
    }
    window.addEventListener("auth:logout", handleAuthLogout);
    return () => window.removeEventListener("auth:logout", handleAuthLogout);
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;

    getDatasetStats()
      .then((data) => {
        setDatasetStats({ data, loading: false, error: null });
        setLastUpdated(new Date());
      })
      .catch(() =>
        setDatasetStats({ data: null, loading: false, error: "Could not load dataset statistics." }),
      );

    getModelPerformance()
      .then((data) => setModelPerformance({ data, loading: false, error: null }))
      .catch(() =>
        setModelPerformance({ data: null, loading: false, error: "Could not load model performance." }),
      );

    getHistory()
      .then((rows) => setResults(rows))
      .catch(() => {
        /* history is a nice-to-have; an empty dashboard is a safe fallback */
      });
  }, [isAuthenticated]);

  async function handleResults(payload) {
    try {
      // Persist first, then reload the full history from the database
      // rather than appending the raw payload locally — this keeps
      // row_index (used as each row's unique id) consistent, since the
      // database assigns it, not the ephemeral per-batch row position.
      await saveHistory(payload.results);
      const freshHistory = await getHistory();
      setResults(freshHistory);
    } catch {
      // If persisting/reloading fails, at least show this prediction locally
      // so the user isn't left staring at nothing — it just won't survive a refresh.
      setResults((previous) => [...previous, ...payload.results]);
    }
  }

  function handleHistoryCleared() {
    setResults([]);
  }

  async function handleLogout() {
    await apiLogout();
    setIsAuthenticated(false);
    setResults([]);
  }

  if (!isAuthenticated) {
    return <Login onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  const totalRecords = datasetStats.data
    ? (datasetStats.data.fault_distribution.Normal || 0) + (datasetStats.data.fault_distribution.Fault || 0)
    : null;

  return (
    <div className="flex h-screen bg-slate-100">
      <Sidebar />

      {/* This column scrolls internally so the sidebar (and header, pinned
          below) stay in view while nav links scroll the page to a section. */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        <div className="sticky top-0 z-10">
          <Header onLogout={handleLogout} />
        </div>

        <main className="flex-1 flex flex-col gap-4 p-6">
          <div id="section-dashboard">
            <InputPanel onResults={handleResults} onHistoryCleared={handleHistoryCleared} />
          </div>

          {/* These sections only make sense once there's a prediction to show,
              so they're hidden entirely instead of showing empty placeholder
              cards — InputPanel above already makes clear what to do first. */}
          {results.length > 0 && (
            <>
              <div id="section-overview">
                <SummaryCards results={results} />
              </div>

              <div id="section-predictions" className="flex flex-col gap-4">
                <FaultProbabilityChart results={results} />
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <PredictionsTable results={results} />
                  <div id="section-alerts">
                    <AlertsPanel results={results} />
                  </div>
                </div>
              </div>

              <div id="section-live-data">
                <OperationalCharts results={results} />
              </div>
            </>
          )}

          <div id="section-analytics" className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <DescriptiveStats
              data={datasetStats.data?.descriptive_stats}
              loading={datasetStats.loading}
              error={datasetStats.error}
            />
            <CorrelationMatrix
              data={datasetStats.data?.correlation_matrix}
              loading={datasetStats.loading}
              error={datasetStats.error}
            />
          </div>

          <div id="section-performance" className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <FaultDistribution
              data={datasetStats.data?.fault_distribution}
              loading={datasetStats.loading}
              error={datasetStats.error}
            />
            <ModelPerformance
              data={modelPerformance.data}
              loading={modelPerformance.loading}
              error={modelPerformance.error}
            />
            <div className="lg:col-span-2">
              <ConfusionMatrix
                data={modelPerformance.data}
                loading={modelPerformance.loading}
                error={modelPerformance.error}
              />
            </div>
          </div>
        </main>

        <div id="section-reports">
          <Footer totalRecords={totalRecords} lastUpdated={lastUpdated} />
        </div>
      </div>
    </div>
  );
}
