import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "@/services/api";
import { API_BASE } from "@/services/apiBase";
import Navbar from "../components/Navbar";
import "../styles/track.css";


const STATUS_CLASS_MAP = {
  Submitted: "submitted",
  "In Progress": "in-progress",
  Resolved: "resolved",
  Rejected: "rejected",
};

function timeAgo(dateValue) {
  if (!dateValue) {
    return "Not available";
  }

  const diffMinutes = Math.max(
    0,
    Math.floor((Date.now() - new Date(dateValue).getTime()) / 60000),
  );

  if (diffMinutes < 1) {
    return "just now";
  }

  if (diffMinutes < 60) {
    return `${diffMinutes} min ago`;
  }

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} hr ago`;
  }

  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} day${diffDays === 1 ? "" : "s"} ago`;
}

function formatDateTime(value) {
  if (!value) {
    return "Pending";
  }

  return new Date(value).toLocaleString();
}

export default function TrackComplaint() {
  const { complaint_number } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloadingReceipt, setDownloadingReceipt] = useState(false);

  useEffect(() => {
    if (!complaint_number) {
      setLoading(false);
      setError("No complaint found. Please check your ID.");
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      setError("");

      try {
        const response = await api(
          `${API_BASE}/api/complaints/${encodeURIComponent(complaint_number)}`,
          {},
        );
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(payload?.detail || "No complaint found. Please check your ID.");
        }
        setData(payload);
      } catch (fetchError) {
        setData(null);
        setError(fetchError.message || "Unable to fetch complaint details.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [complaint_number]);

  const statusClassName = useMemo(
    () => STATUS_CLASS_MAP[data?.status] || "submitted",
    [data?.status],
  );

  const downloadPDF = async () => {
    if (!data?.id || downloadingReceipt) {
      return;
    }

    const receiptPath = data?.closureReceiptUrl || `/receipt/${encodeURIComponent(data.id)}`;

    setDownloadingReceipt(true);

    try {
      const response = await api(`${API_BASE}${receiptPath}`, {
      });

      if (!response.ok) {
        throw new Error("Download failed");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = data?.closureReceiptUrl
        ? `closure-receipt-${data.id}.pdf`
        : `receipt-${data.id}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      window.alert("Unable to download receipt");
    } finally {
      setDownloadingReceipt(false);
    }
  };

  if (loading) {
    return (
      <div className="track-page">
        <Navbar cta={{ to: "/report", label: "Create Report" }} />
        <main className="app-shell track-page__content">
          <div className="loader-card surface-card">
            <div className="spinner" />
            <p>Fetching complaint details...</p>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="track-page">
        <Navbar cta={{ to: "/report", label: "Create Report" }} />
        <main className="app-shell track-page__content">
          <div className="lookup-card surface-card">
            <h1>Complaint Lookup</h1>
            <p>{error}</p>
            <div className="lookup-links">
              <Link to="/track">Try Another Search</Link>
              <Link to="/home">Back to Home</Link>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="track-page detail-page">
      <Navbar cta={{ to: "/report", label: "Create Report" }} />
      <main className="app-shell app-stack track-page__content">
        <section className="page-intro">
          <h1>Complaint Status</h1>
          <p>Review your current complaint status, official timeline, and the latest case details.</p>
        </section>

        <div className="track-card surface-card">
          <div className="track-head">
            <span>{data.type || "General"}</span>
            <h2>{data.id}</h2>
            <p>Priority: {data.priority || "Standard"}</p>
          </div>

          <div className="status-strip">
            <div className="status-summary">
              <strong>Status</strong>
              <p>Last updated: {timeAgo(data.updatedAt)}</p>
            </div>
            <b className={`status-pill ${statusClassName}`}>{data.status}</b>
          </div>

          <div className="timeline-list" aria-label="Complaint progress timeline">
            {(data.timeline || []).map((item) => (
              <div
                key={item.status}
                className={`timeline-row ${item.complete ? "done" : "wait"}`}
              >
                <div className="timeline-dot" aria-hidden="true" />
                <div className="timeline-copy">
                  <h4>{item.status}</h4>
                  <p>{item.timestamp ? formatDateTime(item.timestamp) : "Pending"}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="detail-grid">
            <article>
              <h5>Complaint ID</h5>
              <p>{data.id}</p>
            </article>
            <article>
              <h5>Type</h5>
              <p>{data.type}</p>
            </article>
            <article>
              <h5>Location</h5>
              <p>{data.location}</p>
            </article>
            <article>
              <h5>Created At</h5>
              <p>{formatDateTime(data.createdAt)}</p>
            </article>
            <article>
              <h5>Last Updated</h5>
              <p>{formatDateTime(data.updatedAt)}</p>
            </article>
            <article>
              <h5>Description</h5>
              <p>{data.description}</p>
            </article>
          </div>

          <div className="track-actions">
            <button
              type="button"
              onClick={downloadPDF}
              disabled={!data?.id || downloadingReceipt}
            >
              {downloadingReceipt
                ? "Downloading..."
                : data?.closureReceiptUrl
                  ? "Download Closure Receipt"
                  : "Download Official Receipt"}
            </button>
            <Link to="/track">Track Another Complaint</Link>
            <Link to="/report">Create New Report</Link>
          </div>
        </div>
      </main>
    </div>
  );
}
