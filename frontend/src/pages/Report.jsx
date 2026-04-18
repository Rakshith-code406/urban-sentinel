import { useEffect, useRef, useState } from "react";
import { MapContainer, Marker, TileLayer, useMap, useMapEvents } from "react-leaflet";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import "../utils/fixLeaflet";
import "../styles/report.css";
import { API_BASE } from "../services/apiBase";
import { clearAuthSession, getAccessToken, getStoredUser } from "../services/session";

const LOCATION_STORAGE_KEY = "urbanSentinelLocation";
const LOCATION_FALLBACK_LABEL = "Location not available";
const CAMERA_CONSTRAINTS = [
  {
    video: {
      facingMode: { exact: "environment" },
      width: { ideal: 1280 },
      height: { ideal: 720 },
    },
    audio: false,
  },
  {
    video: {
      facingMode: { ideal: "environment" },
      width: { ideal: 1280 },
      height: { ideal: 720 },
    },
    audio: false,
  },
  {
    video: {
      facingMode: "user",
      width: { ideal: 1280 },
      height: { ideal: 720 },
    },
    audio: false,
  },
  {
    video: {
      width: { ideal: 1280 },
      height: { ideal: 720 },
    },
    audio: false,
  },
  { video: true, audio: false },
];

const ISSUE_TYPES = [
  "Road Damage",
  "Garbage",
  "Street Light Issue",
  "Water Leakage",
  "Enter Manually",
];

const CATEGORY_OPTIONS = [
  "Road Damage",
  "Garbage",
  "Street Light Issue",
  "Water Leakage",
  "Drainage",
  "Public Safety",
  "General",
];

const typeToCategory = {
  "Road Damage": "Road Damage",
  Garbage: "Garbage",
  "Street Light Issue": "Street Light Issue",
  "Water Leakage": "Water Leakage",
};

function LocationMarker({ position, onPick }) {
  useMapEvents({
    click(event) {
      onPick(event.latlng.lat, event.latlng.lng);
    },
  });

  if (!position) return null;
  return <Marker position={position} />;
}

function MapViewportController({ position }) {
  const map = useMap();

  useEffect(() => {
    if (!position) return;
    map.setView(position, 16, { animate: true });
  }, [map, position]);

  return null;
}

function uploadIssue(formData, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const accessToken = getAccessToken();
    xhr.open("POST", `${API_BASE}/issues`);
    if (accessToken) {
      xhr.setRequestHeader("Authorization", `Bearer ${accessToken}`);
    }

    xhr.upload.onloadstart = () => onProgress(5);
    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable) return;
      const progress = Math.min(95, Math.round((event.loaded / event.total) * 95));
      onProgress(progress);
    };
    xhr.upload.onload = () => onProgress(95);

    xhr.onload = () => {
      let payload = {};
      try {
        payload = xhr.responseText ? JSON.parse(xhr.responseText) : {};
      } catch {
        payload = {};
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress(100);
        resolve(payload);
      } else {
        const detail = payload?.detail || "Failed to submit issue.";
        reject(new Error(typeof detail === "string" ? detail : "Failed to submit issue."));
      }
    };

    xhr.onerror = () => reject(new Error("Network error while submitting issue."));
    xhr.send(formData);
  });
}

async function fetchSubmissionStatus(issueId) {
  const accessToken = getAccessToken();
  const response = await fetch(`${API_BASE}/issues/${issueId}/submission-status`, {
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
  });

  if (!response.ok) {
    throw new Error("Unable to fetch submission status.");
  }

  return response.json();
}

function getBrowserLanguageHeader() {
  if (typeof navigator === "undefined") return "en";
  if (Array.isArray(navigator.languages) && navigator.languages.length) {
    return navigator.languages.filter(Boolean).join(",");
  }
  return navigator.language || "en";
}

function normalizeLocationLabel(value, latitude, longitude) {
  const normalized = String(value || "").trim();
  if (normalized) return normalized;
  if (Number.isFinite(latitude) && Number.isFinite(longitude)) {
    return `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`;
  }
  return LOCATION_FALLBACK_LABEL;
}

export default function Report() {
  const navigate = useNavigate();
  const [locationMode, setLocationMode] = useState("manual");
  const [showLocationMenu, setShowLocationMenu] = useState(false);
  const [title, setTitle] = useState("");
  const [selectedType, setSelectedType] = useState("");
  const [manualTitle, setManualTitle] = useState(false);
  const [category, setCategory] = useState("General");
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [selectedCoords, setSelectedCoords] = useState(null);
  const [mapCenter, setMapCenter] = useState([12.9716, 77.5946]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [showCamera, setShowCamera] = useState(false);
  const [cameraStatus, setCameraStatus] = useState("Starting camera...");
  const [capturedImages, setCapturedImages] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [feedback, setFeedback] = useState("");
  const [alertModal, setAlertModal] = useState({ open: false, title: "", text: "" });
  const [successModal, setSuccessModal] = useState({
    open: false,
    issueId: null,
    complaintNumber: "",
    qrCodeUrl: "",
    receiptUrl: "",
    status: "processing",
    qrReady: false,
    receiptReady: false,
    statusError: "",
  });
  const [activePreview, setActivePreview] = useState(null);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const uploadedFilesRef = useRef([]);
  const deviceCameraInputRef = useRef(null);
  const locationFieldRef = useRef(null);

  useEffect(() => {
    uploadedFilesRef.current = uploadedFiles;
  }, [uploadedFiles]);

  useEffect(() => {
    const accessToken = getAccessToken();
    const user = getStoredUser();
    if (!accessToken || !user) {
      navigate("/login", { replace: true });
    }
  }, [navigate]);

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(LOCATION_STORAGE_KEY) || "null");
      if (
        !stored ||
        (stored.permission !== "granted" && stored.permission !== "manual") ||
        stored.latitude === null ||
        stored.latitude === undefined ||
        stored.longitude === null ||
        stored.longitude === undefined
      ) {
        return;
      }

      const nextCoords = [stored.latitude, stored.longitude];
      setSelectedCoords(nextCoords);
      setMapCenter(nextCoords);
      setLocation(normalizeLocationLabel(stored.label, stored.latitude, stored.longitude));
      setLocationMode("auto");
    } catch {
      // Ignore malformed persisted location and fall back to normal report flow.
    }
  }, []);

  useEffect(() => {
    try {
      const stored = JSON.parse(localStorage.getItem(LOCATION_STORAGE_KEY) || "null");
      if (stored?.permission === "granted") {
        detectLocation(false);
      }
    } catch {
      // Ignore malformed persisted location while trying to refresh device position.
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!locationFieldRef.current?.contains(event.target)) {
        setShowLocationMenu(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === "Escape") {
        setActivePreview(null);
      }
    };

    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, []);

  useEffect(() => {
    return () => {
      uploadedFilesRef.current.forEach(({ previewUrl }) => URL.revokeObjectURL(previewUrl));
      closeCamera();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!successModal.open || !successModal.issueId) return undefined;
    if (successModal.qrReady && successModal.receiptReady) return undefined;

    let cancelled = false;

    const pollStatus = async () => {
      try {
        const payload = await fetchSubmissionStatus(successModal.issueId);
        if (cancelled) return;
        setSuccessModal((current) => ({
          ...current,
          complaintNumber: payload?.complaint_number || current.complaintNumber,
          qrCodeUrl: payload?.qr_code_url ? `${API_BASE}${payload.qr_code_url}` : current.qrCodeUrl,
          receiptUrl: payload?.receipt_url ? `${API_BASE}${payload.receipt_url}` : current.receiptUrl,
          status: payload?.status || current.status,
          qrReady: Boolean(payload?.qr_ready),
          receiptReady: Boolean(payload?.receipt_ready),
          statusError: payload?.error || "",
        }));
      } catch {
        if (!cancelled) {
          setSuccessModal((current) => ({
            ...current,
            statusError: current.statusError || "Still preparing your QR code and receipt.",
          }));
        }
      }
    };

    pollStatus();
    const intervalId = window.setInterval(pollStatus, 1500);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [successModal.open, successModal.issueId, successModal.qrReady, successModal.receiptReady]);

  const reverseGeocode = async (lat, lng) => {
    try {
      const params = new URLSearchParams({
        format: "jsonv2",
        lat: String(lat),
        lon: String(lng),
        zoom: "18",
        addressdetails: "1",
        namedetails: "1",
      });
      const response = await fetch(`https://nominatim.openstreetmap.org/reverse?${params.toString()}`, {
        headers: {
          Accept: "application/json",
          "Accept-Language": getBrowserLanguageHeader(),
        },
      });
      const data = await response.json();
      if (data?.display_name) {
        setLocation(data.display_name);
        localStorage.setItem(
          LOCATION_STORAGE_KEY,
          JSON.stringify({
            permission: "granted",
            latitude: lat,
            longitude: lng,
            label: data.display_name,
          })
        );
      } else {
        const fallbackLabel = normalizeLocationLabel("", lat, lng);
        setLocation(fallbackLabel);
        localStorage.setItem(
          LOCATION_STORAGE_KEY,
          JSON.stringify({
            permission: "granted",
            latitude: lat,
            longitude: lng,
            label: fallbackLabel,
          })
        );
      }
    } catch {
      const fallbackLabel = normalizeLocationLabel("", lat, lng);
      setLocation(fallbackLabel);
      localStorage.setItem(
        LOCATION_STORAGE_KEY,
        JSON.stringify({
          permission: "granted",
          latitude: lat,
          longitude: lng,
          label: fallbackLabel,
        })
      );
    }
  };

  const requestCurrentPosition = (options) =>
    new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, options);
    });

  const geocodeManualLocation = async (query) => {
    const cleaned = query.trim();
    if (cleaned.length < 3) return;

    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=jsonv2&q=${encodeURIComponent(cleaned)}&limit=1&addressdetails=1&namedetails=1`,
        {
          headers: {
            Accept: "application/json",
            "Accept-Language": getBrowserLanguageHeader(),
          },
        }
      );
      const data = await response.json();
      const match = Array.isArray(data) ? data[0] : null;
      if (!match?.lat || !match?.lon) {
        setFeedback("Location not found on the map. Please refine the address.");
        return;
      }

      const lat = Number(match.lat);
      const lng = Number(match.lon);
      setSelectedCoords([lat, lng]);
      setMapCenter([lat, lng]);
      const nextLabel = normalizeLocationLabel(match.display_name || cleaned, lat, lng);
      setLocation(nextLabel);
      setFeedback("Manual location pinned on the map.");
    } catch {
      setFeedback("Unable to pin the manual location right now.");
    }
  };

  const handleMapPick = async (lat, lng) => {
    setSelectedCoords([lat, lng]);
    setMapCenter([lat, lng]);
    await reverseGeocode(lat, lng);
    setFeedback("Map location selected.");
  };

  const detectLocation = async (showFeedback = true) => {
    if (!navigator.geolocation) {
      if (showFeedback) {
        setFeedback("Geolocation is not supported in this browser.");
      }
      return;
    }

    if (showFeedback) {
      setFeedback("Detecting your location...");
    }

    try {
      let position = null;

      try {
        position = await requestCurrentPosition({
          enableHighAccuracy: true,
          timeout: 12000,
          maximumAge: 0,
        });
      } catch {
        position = await requestCurrentPosition({
          enableHighAccuracy: false,
          timeout: 10000,
          maximumAge: 60000,
        });
      }

      const { latitude, longitude } = position.coords;
      setSelectedCoords([latitude, longitude]);
      setMapCenter([latitude, longitude]);
      await reverseGeocode(latitude, longitude);
      if (showFeedback) {
        setFeedback("Current device location detected.");
      }
    } catch {
      if (showFeedback) {
        setFeedback("Location access denied. Enter location manually.");
      }
    }
  };

  const handleLocationModeChange = async (event) => {
    const value = event.target.value;
    setLocationMode(value);
    setShowLocationMenu(false);

    if (value === "auto") {
      await detectLocation(true);
      return;
    }

    setSelectedCoords(null);
    setLocation("");
    setFeedback("Enter the location manually or tap the map to place the pin.");
  };

  const addFiles = (fileList) => {
    const selected = Array.from(fileList || []);
    if (!selected.length) return;

    const toAdd = selected.map((file) => ({
      id: `${file.name}-${file.lastModified}-${Math.random()}`,
      file,
      previewUrl: URL.createObjectURL(file),
    }));

    setUploadedFiles((prev) => [...prev, ...toAdd]);
  };

  const handleFileChange = (event) => {
    addFiles(event.target.files);
    event.target.value = "";
  };

  const handleDeviceCameraCapture = (event) => {
    closeCamera();
    addFiles(event.target.files);
    event.target.value = "";
  };

  const removeUploadedFile = (id) => {
    setUploadedFiles((prev) => {
      const item = prev.find((f) => f.id === id);
      if (item) URL.revokeObjectURL(item.previewUrl);
      return prev.filter((file) => file.id !== id);
    });
  };

  const stopStream = (stream) => {
    stream?.getTracks().forEach((track) => track.stop());
  };

  const waitForVideoReady = (video) =>
    new Promise((resolve, reject) => {
      let settled = false;

      const cleanup = () => {
        clearTimeout(timeoutId);
        video.onloadedmetadata = null;
        video.oncanplay = null;
        video.onerror = null;
      };

      const finish = (callback) => {
        if (settled) return;
        settled = true;
        cleanup();
        callback();
      };

      const maybeReady = () => {
        if (video.readyState >= 2 && video.videoWidth > 0 && video.videoHeight > 0) {
          finish(resolve);
        }
      };

      const timeoutId = window.setTimeout(() => {
        finish(() => reject(new Error("Camera preview did not become ready in time.")));
      }, 3500);

      video.onloadedmetadata = maybeReady;
      video.oncanplay = maybeReady;
      video.onerror = () => finish(() => reject(new Error("Camera preview failed to load.")));
      maybeReady();
    });

  const attachStreamToVideo = async (stream) => {
    const video = videoRef.current;
    if (!video) throw new Error("Camera preview is unavailable.");

    video.srcObject = stream;
    video.muted = true;
    video.setAttribute("playsinline", "true");
    await video.play().catch(() => {});
    await waitForVideoReady(video);
  };

  const startCameraStream = async () => {
    let lastError = null;

    for (const constraints of CAMERA_CONSTRAINTS) {
      let stream = null;

      try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        await attachStreamToVideo(stream);
        return stream;
      } catch (error) {
        lastError = error;
        stopStream(stream);
      }
    }

    throw lastError || new Error("Unable to access camera.");
  };

  const openCamera = async () => {
    if (!navigator.mediaDevices?.getUserMedia) {
      deviceCameraInputRef.current?.click();
      return;
    }

    try {
      closeCamera();
      setShowCamera(true);
      setCameraStatus("Starting camera...");
      await startCameraStream();
      setCameraStatus("Camera ready. Capture the photo when the preview looks correct.");
      setFeedback("Live camera opened.");
    } catch {
      setShowCamera(false);
      closeCamera();
      deviceCameraInputRef.current?.click();
      setFeedback(
        "Live camera preview was not stable on this device. Opening device camera upload instead."
      );
    }
  };

  const closeCamera = () => {
    const stream = videoRef.current?.srcObject;
    stopStream(stream);
    if (videoRef.current) {
      videoRef.current.pause();
      videoRef.current.srcObject = null;
    }
    setCameraStatus("Starting camera...");
    setShowCamera(false);
  };

  const capturePhoto = () => {
    const canvas = canvasRef.current;
    const video = videoRef.current;
    if (!canvas || !video) return;
    if (!video.videoWidth || !video.videoHeight) {
      setAlertModal({
        open: true,
        title: "Camera not ready",
        text: "Please wait for the camera preview, then capture the photo again.",
      });
      return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);

    const imageData = canvas.toDataURL("image/png");
    setCapturedImages((prev) => [...prev, imageData]);
  };

  const deleteCapturedImage = (index) => {
    setCapturedImages((prev) => prev.filter((_, idx) => idx !== index));
  };

  const resetForm = () => {
    setTitle("");
    setSelectedType("");
    setManualTitle(false);
    setCategory("General");
    setLocationMode("manual");
    setDescription("");
    setLocation("");
    setSelectedCoords(null);
    setMapCenter([12.9716, 77.5946]);
    uploadedFilesRef.current.forEach(({ previewUrl }) => URL.revokeObjectURL(previewUrl));
    setUploadedFiles([]);
    setCapturedImages([]);
    setUploadProgress(0);
    setShowLocationMenu(false);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    const finalTitle = manualTitle ? title.trim() : selectedType;
    const normalizedCategory = category.trim();
    const normalizedLocation = location.trim();
    const normalizedDescription = description.trim();

    const requiredFields = [
      { value: finalTitle, label: "Issue Title" },
      { value: normalizedCategory, label: "Category" },
      { value: normalizedLocation, label: "Location" },
      { value: normalizedDescription, label: "Description" },
    ];
    const missingField = requiredFields.find(({ value }) => !value);

    if (missingField) {
      setAlertModal({
        open: true,
        title: "Field required",
        text: `${missingField.label} is required.`,
      });
      return;
    }

    if (normalizedDescription.length < 10) {
      setAlertModal({
        open: true,
        title: "Description too short",
        text: "Description must be at least 10 characters.",
      });
      return;
    }

    setSubmitting(true);
    setUploadProgress(0);
    setFeedback("Submitting your report...");

    try {
      const formData = new FormData();
      formData.append("title", finalTitle);
      formData.append("description", normalizedDescription);
      formData.append("location", normalizedLocation);
      formData.append("category", normalizedCategory);

      uploadedFiles.forEach(({ file }) => formData.append("files", file));

      for (const [index, image] of capturedImages.entries()) {
        const blob = await fetch(image).then((res) => res.blob());
        formData.append("files", blob, `camera-${index + 1}.png`);
      }

      const payload = await uploadIssue(formData, setUploadProgress);

      const issueId = payload?.issue_id || payload?.report_id || null;
      const complaintNumber = payload?.complaint_number || "";
      setFeedback("Issue submitted successfully.");
      setSuccessModal({
        open: true,
        issueId,
        complaintNumber,
        qrCodeUrl: payload?.submission_status?.qr_code_url
          ? `${API_BASE}${payload.submission_status.qr_code_url}`
          : "",
        receiptUrl: payload?.submission_status?.receipt_url
          ? `${API_BASE}${payload.submission_status.receipt_url}`
          : "",
        status: payload?.submission_status?.status || "processing",
        qrReady: Boolean(payload?.submission_status?.qr_ready),
        receiptReady: Boolean(payload?.submission_status?.receipt_ready),
        statusError: payload?.submission_status?.error || "",
      });
      resetForm();
    } catch (error) {
      if ((error.message || "").toLowerCase().includes("authentication required")) {
        clearAuthSession();
      }
      setAlertModal({
        open: true,
        title: "Submission failed",
        text: error.message || "Submission failed.",
      });
    } finally {
      setSubmitting(false);
      setUploadProgress((value) => (value < 100 ? 0 : value));
    }
  };

  return (
    <div className="report-page">
      <Navbar cta={{ to: "/home", label: "Back to Dashboard" }} />
      <main className="app-shell app-stack report-page__content">
      {alertModal.open && (
        <div className="report-alert-modal" role="presentation">
          <div
            className="report-alert-card"
            role="dialog"
            aria-modal="true"
            aria-labelledby="report-alert-title"
          >
            <p className="report-alert-eyebrow">Attention</p>
            <h3 id="report-alert-title">{alertModal.title}</h3>
            <p>{alertModal.text}</p>
            <button
              type="button"
              onClick={() => setAlertModal({ open: false, title: "", text: "" })}
            >
              Close
            </button>
          </div>
        </div>
      )}

      <section className="report-hero page-intro">
        <h1>Report a Civic Issue</h1>
        <p>Submit complete reports with map location, photo proof, and category tags.</p>
      </section>

      <section className="report-layout">
        <form className="report-panel surface-card" onSubmit={handleSubmit}>
          <div className="panel-head">
            <h2>Issue Details</h2>
            <span>Urban Sentinel Intake</span>
          </div>

          <div className="title-row">
            <input
              type="text"
              placeholder="Issue Title"
              value={manualTitle ? title : selectedType}
              onChange={(event) => setTitle(event.target.value)}
              disabled={!manualTitle}
            />

            <select
              value={manualTitle ? "Enter Manually" : selectedType}
              onChange={(event) => {
                const value = event.target.value;
                if (value === "Enter Manually") {
                  setManualTitle(true);
                  setSelectedType("");
                  return;
                }

                setManualTitle(false);
                setSelectedType(value);
                if (typeToCategory[value]) {
                  setCategory(typeToCategory[value]);
                }
              }}
            >
              <option value="">Select Type</option>
              {ISSUE_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          <div className="field-grid">
            <div>
              <label>Category</label>
              <select value={category} onChange={(event) => setCategory(event.target.value)}>
                {CATEGORY_OPTIONS.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </div>

            <div
              className={`location-field-wrap ${showLocationMenu ? "menu-open" : ""}`}
              ref={locationFieldRef}
            >
              <label>Location</label>
              <div className="location-single-field">
                <input
                  className="location-single-input"
                  type="text"
                  placeholder="Location"
                  value={location}
                  onChange={(event) => setLocation(event.target.value)}
                  onFocus={() => setShowLocationMenu(true)}
                  onClick={() => setShowLocationMenu(true)}
                  onBlur={() => {
                    if (locationMode === "manual") {
                      geocodeManualLocation(location);
                    }
                  }}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && locationMode === "manual") {
                      event.preventDefault();
                      geocodeManualLocation(location);
                    }
                  }}
                />
                <button
                  type="button"
                  className="location-menu-toggle"
                  onClick={() => setShowLocationMenu((value) => !value)}
                  aria-label="Choose location mode"
                >
                  ▾
                </button>
                {showLocationMenu && (
                  <div className="location-menu">
                    <button
                      type="button"
                      className={locationMode === "auto" ? "active" : ""}
                      onClick={() =>
                        handleLocationModeChange({ target: { value: "auto" } })
                      }
                    >
                      Auto Detect Location
                    </button>
                    <button
                      type="button"
                      className={locationMode === "manual" ? "active" : ""}
                      onClick={() =>
                        handleLocationModeChange({ target: { value: "manual" } })
                      }
                    >
                      Enter Manually
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="location-actions">
            {locationMode === "auto" ? (
              <>
                <button type="button" className="ghost-btn" onClick={detectLocation}>
                  Refresh Detected Location
                </button>
                <p>Tip: The map opens around your detected position. Tap the map only if you need to adjust it.</p>
              </>
            ) : (
              <p>Tip: Enter the address and press Enter, click outside, or tap the map to pin the exact location.</p>
            )}
          </div>

          <div className="map-shell">
            <MapContainer
              center={mapCenter}
              zoom={selectedCoords ? 16 : 13}
              scrollWheelZoom={false}
              style={{ height: "100%" }}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <MapViewportController position={selectedCoords} />
              <LocationMarker position={selectedCoords} onPick={handleMapPick} />
            </MapContainer>
          </div>

          <label>Description</label>
          <textarea
            name="description"
            placeholder="Describe what happened, severity, and any urgency."
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            required
            minLength={10}
          />

          <div
            className={`dropzone ${isDragging ? "dropzone-active" : ""}`}
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={(event) => {
              event.preventDefault();
              setIsDragging(false);
            }}
            onDrop={(event) => {
              event.preventDefault();
              setIsDragging(false);
              addFiles(event.dataTransfer.files);
            }}
          >
            <strong>Drag and drop files here</strong>
            <span>or</span>
            <label className="upload-btn">
              Browse Files
              <input type="file" multiple onChange={handleFileChange} />
            </label>
            <input
              ref={deviceCameraInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleDeviceCameraCapture}
              hidden
            />
          </div>

          <div className="media-actions">
            <button type="button" className="camera-btn" onClick={openCamera}>
              Open Camera
            </button>
            <button
              type="button"
              className="camera-btn camera-btn-secondary"
              onClick={() => deviceCameraInputRef.current?.click()}
            >
              Upload from Device
            </button>
          </div>

          <div className="preview-grid">
            {uploadedFiles.map((item) => (
              <div key={item.id} className="preview-wrapper">
                <button
                  type="button"
                  className="preview-image-button"
                  onClick={() => setActivePreview({ src: item.previewUrl, alt: item.file.name })}
                  aria-label={`Preview ${item.file.name}`}
                >
                  <img src={item.previewUrl} alt={item.file.name} />
                </button>
                <button type="button" aria-label={`Remove file ${item.file.name}`} onClick={() => removeUploadedFile(item.id)}>
                  Remove
                </button>
              </div>
            ))}

            {capturedImages.map((image, index) => (
              <div key={`camera-${index}`} className="preview-wrapper">
                <button
                  type="button"
                  className="preview-image-button"
                  onClick={() => setActivePreview({ src: image, alt: `Capture ${index + 1}` })}
                  aria-label={`Preview capture ${index + 1}`}
                >
                  <img src={image} alt={`Capture ${index + 1}`} />
                </button>
                <button type="button" aria-label={`Remove capture ${index + 1}`} onClick={() => deleteCapturedImage(index)}>
                  Remove
                </button>
              </div>
            ))}
          </div>

          {submitting && (
            <div className="progress-wrap">
              <div className="progress-head">
                <span>Uploading evidence</span>
                <strong>{uploadProgress}%</strong>
              </div>
              <div className="progress-track">
                <div className="progress-bar" style={{ width: `${uploadProgress}%` }} />
              </div>
            </div>
          )}

          {feedback && <p className="feedback-text">{feedback}</p>}

          <button type="submit" className="submit-btn" disabled={submitting}>
            {submitting ? "Submitting..." : "Submit Issue"}
          </button>
        </form>
      </section>

      {showCamera && (
        <div className="camera-modal">
          <div className="camera-content">
            <h3>Capture Evidence</h3>
            <p>{cameraStatus}</p>
            <video ref={videoRef} autoPlay playsInline muted />
            <canvas ref={canvasRef} style={{ display: "none" }} />
            <div className="camera-controls">
              <button type="button" onClick={capturePhoto}>
                Capture
              </button>
              <button type="button" onClick={closeCamera}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {successModal.open && (
        <div className="success-modal">
          <div className="success-card">
            <div className="check-anim">
              <span className="check-circle" />
              <span className="check-mark" />
            </div>
            <h3>Report Submitted</h3>
            <p>Your complaint has been registered successfully.</p>
            <strong>{successModal.complaintNumber}</strong>
            {!successModal.qrReady && (
              <p>Preparing your QR code and receipt in the background...</p>
            )}
            {successModal.statusError && (
              <p>{successModal.statusError}</p>
            )}
            {successModal.qrReady && successModal.qrCodeUrl && (
              <div className="success-qr-wrap">
                <img src={successModal.qrCodeUrl} alt="Complaint QR" />
                <p>Scan this QR to open live complaint status on any device.</p>
              </div>
            )}
            <div className="success-actions">
              <button
                type="button"
                onClick={() => {
                  setSuccessModal({
                    open: false,
                    issueId: null,
                    complaintNumber: "",
                    qrCodeUrl: "",
                    receiptUrl: "",
                    status: "processing",
                    qrReady: false,
                    receiptReady: false,
                    statusError: "",
                  });
                  navigate("/home");
                }}
              >
                Close
              </button>
              {successModal.receiptReady && successModal.receiptUrl ? (
                <a
                  href={successModal.receiptUrl}
                  target="_blank"
                  rel="noreferrer"
                >
                  Download Receipt
                </a>
              ) : (
                <span>Receipt is being generated...</span>
              )}
            </div>
          </div>
        </div>
      )}

      {activePreview && (
        <div
          className="image-preview-modal"
          role="presentation"
          onClick={() => setActivePreview(null)}
        >
          <div
            className="image-preview-card"
            role="dialog"
            aria-modal="true"
            aria-label="Image preview"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              className="image-preview-close"
              onClick={() => setActivePreview(null)}
              aria-label="Close image preview"
            >
              Close
            </button>
            <img src={activePreview.src} alt={activePreview.alt} />
          </div>
        </div>
      )}
      </main>
    </div>
  );
}
