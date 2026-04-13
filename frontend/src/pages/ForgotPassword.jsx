import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "../services/auth";
import "../styles/auth.css";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [otpDigits, setOtpDigits] = useState(["", "", "", "", "", ""]);
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [step, setStep] = useState(1);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [resendIn, setResendIn] = useState(0);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const otpRefs = useRef([]);

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

  const passwordStrength = getPasswordStrength(newPassword);
  const getFinalEmail = () => email.trim();

  const requestCode = async (event) => {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      const payload = await authApi.requestForgotPassword({ email: getFinalEmail() });
      setStep(2);
      setMessage(payload.detail || payload.message || "OTP sent. Check system console.");
      setResendIn(60);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (resendIn <= 0) return;
    const timer = setTimeout(() => setResendIn((value) => value - 1), 1000);
    return () => clearTimeout(timer);
  }, [resendIn]);

  const handleResend = async () => {
    if (resendIn > 0 || loading) return;
    setLoading(true);
    setMessage("");
    try {
      const payload = await authApi.requestForgotPassword({ email: getFinalEmail() });
      setMessage(payload.detail || payload.message || "OTP sent. Check system console.");
      setOtpDigits(["", "", "", "", "", ""]);
      otpRefs.current[0]?.focus();
      setResendIn(60);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  const verifyCode = async (event) => {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      const code = otpDigits.join("");
      if (code.length !== 6) {
        setMessage("Enter the 6 digit verification code");
        setLoading(false);
        return;
      }
      const payload = await authApi.verifyForgotPassword({ email: getFinalEmail(), otp: code });
      if (payload.status !== "success") {
        throw new Error(payload.message || "OTP verification failed");
      }
      setStep(3);
      setMessage("OTP verified");
    } catch (error) {
      setMessage(error.message || "OTP verification failed");
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index, value) => {
    const next = value.replace(/\D/g, "").slice(-1);
    const updated = [...otpDigits];
    updated[index] = next;
    setOtpDigits(updated);
    if (next && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
  };

  const handleOtpKeyDown = (index, event) => {
    if (event.key === "Backspace" && !otpDigits[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const resetPassword = async (event) => {
    event.preventDefault();
    if (newPassword !== confirmPassword) {
      setMessage("Password and confirm password must match");
      return;
    }

    setLoading(true);
    setMessage("");
    try {
      await authApi.resetForgotPassword({
        email: getFinalEmail(),
        otp: otpDigits.join(""),
        new_password: newPassword,
      });
      setMessage("Password reset successful. Please login.");
      setTimeout(() => navigate("/login"), 800);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <section className="auth-shell">
        <aside className="auth-brand">
          <h2>Urban Sentinel</h2>
          <h3>Password Recovery</h3>
          <p>Recover access securely using your registered email address.</p>
        </aside>

        <div className="auth-card">
          <h1>Forgot Password</h1>
          <p>Verify with your registered email and reset your password.</p>

        {step === 1 && (
          <form onSubmit={requestCode}>
            <label htmlFor="forgot-identifier">Registered Email</label>
            <input
              id="forgot-identifier"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Registered email"
              required
            />
            {message && <p className="auth-message">{message}</p>}
            <button type="submit" disabled={loading}>{loading ? "Sending..." : "Send Verification Code"}</button>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={verifyCode}>
            <label htmlFor="otp-digit-0">Enter Verification Code</label>
            <div className="otp-grid">
              {otpDigits.map((digit, index) => (
                <input
                  key={index}
                  id={`otp-digit-${index}`}
                  ref={(el) => (otpRefs.current[index] = el)}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(event) => handleOtpChange(index, event.target.value)}
                  onKeyDown={(event) => handleOtpKeyDown(index, event)}
                  className="otp-input"
                  required
                />
              ))}
            </div>
            <div className="resend-row">
              <button
                type="button"
                className="resend-btn"
                onClick={handleResend}
                disabled={resendIn > 0 || loading}
              >
                {resendIn > 0 ? `Resend OTP in ${resendIn}s` : "Resend OTP"}
              </button>
            </div>
            {message && <p className="auth-message">{message}</p>}
            <button type="submit" disabled={loading}>{loading ? "Verifying..." : "Verify Code"}</button>
          </form>
        )}

        {step === 3 && (
          <form onSubmit={resetPassword}>
            <label htmlFor="forgot-new-password">New Password</label>
            <input
              id="forgot-new-password"
              type={showPassword ? "text" : "password"}
              autoComplete="new-password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
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
            <label htmlFor="forgot-confirm-password">Confirm New Password</label>
            <input
              id="forgot-confirm-password"
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
            {message && <p className="auth-message">{message}</p>}
            <button type="submit" disabled={loading}>{loading ? "Updating..." : "Reset Password"}</button>
          </form>
        )}

          <p className="auth-footer">
            Remembered password? <Link to="/login">Back to login</Link>
          </p>
        </div>
      </section>
    </div>
  );
}
