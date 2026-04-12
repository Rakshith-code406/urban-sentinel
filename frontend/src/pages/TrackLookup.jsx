import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "@/services/api";
import { API_BASE } from "@/services/apiBase";
import Navbar from "../components/Navbar";
import "../styles/track.css";


const TRACK_BY_ID = "id";
const TRACK_BY_MOBILE = "mobile";
const COMPLAINT_ID_PATTERN = /^US-(?:\d{4}-)?\d{4,}$/i;

function normalizePhone(value) {
  return value.replace(/\D/g, "");
}

export default function TrackLookup() {
  const [activeTab, setActiveTab] = useState(TRACK_BY_ID);
  const [complaintNumber, setComplaintNumber] = useState("");
  const [mobileNumber, setMobileNumber] = useState("");
  const [error, setError] = useState("");
  const [loadingMobile, setLoadingMobile] = useState(false);
  const [mobileResults, setMobileResults] = useState([]);
  const navigate = useNavigate();

  const hasMobileResults = useMemo(() => mobileResults.length > 0, [mobileResults]);

  const resetFeedback = () => {
    setError("");
    setMobileResults([]);
  };

  const handleTrackById = (event) => {
    event.preventDefault();
    const normalized = complaintNumber.trim().toUpperCase();

    if (!normalized) {
      setError("Please enter complaint number.");
      return;
    }

    if (!COMPLAINT_ID_PATTERN.test(normalized)) {
      setError("Enter a valid complaint ID in the format US-0001.");
      return;
    }

    setError("");
    navigate(`/track/${normalized}`);
  };

  const handleTrackByMobile = async (event) => {
    event.preventDefault();
    const normalized = normalizePhone(mobileNumber);

    if (!normalized) {
      setError("Please enter mobile number.");
      return;
    }

    if (normalized.length < 10) {
      setError("Enter a valid mobile number.");
      return;
    }

    setLoadingMobile(true);
    setError("");
    setMobileResults([]);

    try {
      const response = await api(
        `${API_BASE}/api/complaints/mobile/${encodeURIComponent(normalized)}`,
        {},
      );

      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload?.detail || "Unable to fetch complaint details.");
      }

      const complaints = Array.isArray(payload?.complaints) ? payload.complaints : [];
      if (!complaints.length) {
        setError("No complaint found. Please check your mobile number.");
        return;
      }

      setMobileResults(complaints);
    } catch (fetchError) {
      setError(fetchError.message || "Unable to fetch complaint details.");
    } finally {
      setLoadingMobile(false);
    }
  };

  return (
    <div className="track-page lookup-page">
      <Navbar cta={{ to: "/report", label: "Create Report" }} />
      <main className="app-shell app-stack track-page__content">
        <section className="page-intro">
          <h1>Track Your Complaint</h1>
          <p>Use your complaint ID or verified mobile number to review status, timeline, and official progress.</p>
        </section>

        <div className="lookup-card surface-card">
          <div className="track-tabs" role="tablist" aria-label="Complaint tracking options">
            <button
              type="button"
              className={`track-tab ${activeTab === TRACK_BY_ID ? "active" : ""}`}
              role="tab"
              aria-selected={activeTab === TRACK_BY_ID}
              onClick={() => {
                setActiveTab(TRACK_BY_ID);
                resetFeedback();
              }}
            >
              Track by ID
            </button>
            <button
              type="button"
              className={`track-tab ${activeTab === TRACK_BY_MOBILE ? "active" : ""}`}
              role="tab"
              aria-selected={activeTab === TRACK_BY_MOBILE}
              onClick={() => {
                setActiveTab(TRACK_BY_MOBILE);
                resetFeedback();
              }}
            >
              Track by Mobile
            </button>
          </div>

          <h2>Complaint Lookup</h2>
          <p>
            {activeTab === TRACK_BY_ID
              ? "Enter your official complaint ID to open the full tracking view."
              : "Enter your verified mobile number to securely see complaints linked to your account."}
          </p>

          {activeTab === TRACK_BY_ID ? (
            <form onSubmit={handleTrackById}>
              <label className="sr-only" htmlFor="complaint-number">Complaint Number</label>
              <input
                id="complaint-number"
                type="text"
                placeholder="US-0001"
                value={complaintNumber}
                onChange={(event) => {
                  setComplaintNumber(event.target.value.toUpperCase());
                  if (error) {
                    setError("");
                  }
                }}
              />
              {error && <small>{error}</small>}
              <button type="submit">View Complaint</button>
            </form>
          ) : (
            <form onSubmit={handleTrackByMobile}>
              <label className="sr-only" htmlFor="mobile-number">Mobile Number</label>
              <input
                id="mobile-number"
                type="tel"
                inputMode="numeric"
                placeholder="Verified mobile number"
                value={mobileNumber}
                onChange={(event) => {
                  setMobileNumber(normalizePhone(event.target.value));
                  if (error) {
                    setError("");
                  }
                }}
              />
              {error && <small>{error}</small>}
              <button type="submit" disabled={loadingMobile}>
                {loadingMobile ? "Fetching complaint details..." : "View Complaints"}
              </button>
            </form>
          )}

          <div className="lookup-links">
            <Link to="/report">Create New Report</Link>
            <Link to="/home">Back to Home</Link>
          </div>
        </div>

        {activeTab === TRACK_BY_MOBILE ? (
          <section className="track-card surface-card">
            <div className="track-head">
              <span>Verified Lookup</span>
              <h2>Complaints Linked to Mobile</h2>
              <p>
                {loadingMobile
                  ? "Fetching complaint details..."
                  : hasMobileResults
                    ? "Open a complaint to view its complete timeline and details."
                    : "Only complaints linked to your verified mobile number will appear here."}
              </p>
            </div>

            {hasMobileResults ? (
              <div className="mobile-results">
                {mobileResults.map((complaint) => (
                  <article key={complaint.id} className="mobile-result-card">
                    <div className="mobile-result-row">
                      <strong>{complaint.id}</strong>
                      <span className={`status-pill ${String(complaint.status || "").toLowerCase().replace(/\s+/g, "-")}`}>
                        {complaint.status}
                      </span>
                    </div>
                    <p>{complaint.title || complaint.type}</p>
                    <div className="mobile-result-meta">
                      <span>{complaint.type}</span>
                      <span>{complaint.location}</span>
                    </div>
                    <Link to={`/track/${complaint.id}`}>View Complaint</Link>
                  </article>
                ))}
              </div>
            ) : null}
          </section>
        ) : null}
      </main>
    </div>
  );
}
