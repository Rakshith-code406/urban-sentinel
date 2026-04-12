import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "../services/auth";
import "../styles/auth.css";

const COUNTRY_CODES = ["+91", "+1", "+44", "+61", "+971", "+65"];

export default function Register() {
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [countryCode, setCountryCode] = useState("+91");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [alertModal, setAlertModal] = useState({ open: false, title: "", text: "" });

  const getPasswordStrength = (value) => {
    if (value.length < 6) return { label: "Weak", score: 25 };
    let score = 40;
    if (/[A-Z]/.test(value)) score += 20;
    if (/[0-9]/.test(value)) score += 20;
    if (/[^A-Za-z0-9]/.test(value)) score += 20;
    if (value.length >= 10) score += 10;
    if (score >= 85) return { label: "Strong", score: 100 };
    if (score >= 60) return { label: "Medium", score };
    return { label: "Weak", score };
  };

  const passwordStrength = getPasswordStrength(password);

  useEffect(() => {
    if (!showSuccessModal) return undefined;

    const redirectTimer = window.setTimeout(() => {
      navigate("/login");
    }, 1800);

    return () => window.clearTimeout(redirectTimer);
  }, [navigate, showSuccessModal]);

  const openAlert = (title, text) => {
    setAlertModal({ open: true, title, text });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (password !== confirmPassword) {
      openAlert("Registration error", "Confirm Password is required to match Password.");
      return;
    }

    setLoading(true);

    try {
      await authApi.register({
        full_name: fullName,
        email,
        phone: `${countryCode}${phone}`,
        password,
      });
      localStorage.setItem(
        "rememberedLoginProfile",
        JSON.stringify({
          identifier: email,
          email,
          countryCode,
          phone,
          phoneWithCode: `${countryCode}${phone}`,
          password,
          source: "register",
          savedAt: new Date().toISOString(),
        })
      );
      setFullName("");
      setEmail("");
      setCountryCode("+91");
      setPhone("");
      setPassword("");
      setConfirmPassword("");
      setShowPassword(false);
      setShowConfirmPassword(false);
      setShowSuccessModal(true);
    } catch (error) {
      const errorText =
        error.message?.toLowerCase().includes("already registered")
          ? "User already registered."
          : error.message || "Unable to complete registration.";
      openAlert("Registration error", errorText);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      {alertModal.open && (
        <div className="auth-modal-backdrop" role="presentation">
          <div
            className="auth-alert-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="register-alert-title"
          >
            <p className="auth-alert-eyebrow">Attention</p>
            <h2 id="register-alert-title">{alertModal.title}</h2>
            <p className="auth-alert-text">{alertModal.text}</p>
            <button
              type="button"
              onClick={() => setAlertModal({ open: false, title: "", text: "" })}
            >
              Close
            </button>
          </div>
        </div>
      )}

      {showSuccessModal && (
        <div className="auth-modal-backdrop" role="presentation">
          <div
            className="auth-success-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="register-success-title"
          >
            <div className="auth-success-icon" aria-hidden="true">
              OK
            </div>
            <p className="auth-success-eyebrow">Account Created</p>
            <h2 id="register-success-title">Registered successfully</h2>
            <p className="auth-success-text">
              Your Urban Sentinel account has been created successfully. Redirecting you to the
              login page.
            </p>
            <button type="button" onClick={() => navigate("/login")}>
              Continue to Login
            </button>
          </div>
        </div>
      )}

      <section className="auth-shell">
        <aside className="auth-brand">
          <h2>Urban Sentinel</h2>
          <h3>New User Registration</h3>
          <p>Create your account to file complaints and receive verified updates.</p>
        </aside>

        <div className="auth-card">
          <h1>Urban Sentinel Register</h1>
          <p>Provide the required details to create your account.</p>

          <form onSubmit={handleSubmit}>
            <label htmlFor="register-full-name">Full Name</label>
            <input
              id="register-full-name"
              type="text"
              autoComplete="name"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              required
            />

            <label htmlFor="register-email">Email</label>
            <input
              id="register-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />

            <label htmlFor="register-phone">Phone Number</label>
            <div className="phone-row">
              <select aria-label="Country code" value={countryCode} onChange={(event) => setCountryCode(event.target.value)}>
                {COUNTRY_CODES.map((code) => (
                  <option key={code} value={code}>
                    {code}
                  </option>
                ))}
              </select>
              <input
                id="register-phone"
                type="tel"
                autoComplete="tel-national"
                value={phone}
                onChange={(event) => setPhone(event.target.value.replace(/\D/g, ""))}
                placeholder="Phone number"
                required
              />
            </div>

            <label htmlFor="register-password">Password</label>
            <input
              id="register-password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowPassword((value) => !value)}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
            <div className="strength-wrap">
              <div className="strength-track">
                <div className="strength-bar" style={{ width: `${passwordStrength.score}%` }} />
              </div>
              <small>Password Strength: {passwordStrength.label}</small>
            </div>

            <label htmlFor="register-confirm-password">Confirm Password</label>
            <input
              id="register-confirm-password"
              type={showConfirmPassword ? "text" : "password"}
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              required
            />
            <button
              type="button"
              className="password-toggle"
              onClick={() => setShowConfirmPassword((value) => !value)}
            >
              {showConfirmPassword ? "Hide" : "Show"}
            </button>

            <button type="submit" disabled={loading}>
              {loading ? "Creating..." : "Register"}
            </button>
          </form>

          <p className="auth-footer">
            Already have an account? <Link to="/login">Login</Link>
          </p>
        </div>
      </section>
    </div>
  );
}
