"use client";

import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Eye,
  EyeOff,
  Mail,
  Phone,
  Sparkles,
  ShieldCheck,
  FileText,
  MailOpen,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { apiUrl } from "@/services/apiBase";
import { authApi } from "@/services/auth";
import { prefetchDashboardBootstrap } from "@/services/dashboardCache";
import RippleButton from "@/components/ui/ripple-button";
import { setAuthSession } from "@/services/session";

interface PupilProps {
  size?: number;
  maxDistance?: number;
  pupilColor?: string;
  forceLookX?: number;
  forceLookY?: number;
}

const Pupil = ({ 
  size = 12, 
  maxDistance = 5,
  pupilColor = "black",
  forceLookX,
  forceLookY
}: PupilProps) => {
  const [mouseX, setMouseX] = useState<number>(0);
  const [mouseY, setMouseY] = useState<number>(0);
  const pupilRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMouseX(e.clientX);
      setMouseY(e.clientY);
    };

    window.addEventListener("mousemove", handleMouseMove);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  const calculatePupilPosition = () => {
    if (!pupilRef.current) return { x: 0, y: 0 };

    if (forceLookX !== undefined && forceLookY !== undefined) {
      return { x: forceLookX, y: forceLookY };
    }

    const pupil = pupilRef.current.getBoundingClientRect();
    const pupilCenterX = pupil.left + pupil.width / 2;
    const pupilCenterY = pupil.top + pupil.height / 2;

    const deltaX = mouseX - pupilCenterX;
    const deltaY = mouseY - pupilCenterY;
    const distance = Math.min(Math.sqrt(deltaX ** 2 + deltaY ** 2), maxDistance);

    const angle = Math.atan2(deltaY, deltaX);
    const x = Math.cos(angle) * distance;
    const y = Math.sin(angle) * distance;

    return { x, y };
  };

  const pupilPosition = calculatePupilPosition();

  return (
    <div
      ref={pupilRef}
      className="rounded-full"
      style={{
        width: `${size}px`,
        height: `${size}px`,
        backgroundColor: pupilColor,
        transform: `translate(${pupilPosition.x}px, ${pupilPosition.y}px)`,
        transition: 'transform 0.1s ease-out',
      }}
    />
  );
};

interface EyeBallProps {
  size?: number;
  pupilSize?: number;
  maxDistance?: number;
  eyeColor?: string;
  pupilColor?: string;
  isBlinking?: boolean;
  forceLookX?: number;
  forceLookY?: number;
}

const EyeBall = ({ 
  size = 48, 
  pupilSize = 16, 
  maxDistance = 10,
  eyeColor = "white",
  pupilColor = "black",
  isBlinking = false,
  forceLookX,
  forceLookY
}: EyeBallProps) => {
  const [mouseX, setMouseX] = useState<number>(0);
  const [mouseY, setMouseY] = useState<number>(0);
  const eyeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMouseX(e.clientX);
      setMouseY(e.clientY);
    };

    window.addEventListener("mousemove", handleMouseMove);

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  const calculatePupilPosition = () => {
    if (!eyeRef.current) return { x: 0, y: 0 };

    if (forceLookX !== undefined && forceLookY !== undefined) {
      return { x: forceLookX, y: forceLookY };
    }

    const eye = eyeRef.current.getBoundingClientRect();
    const eyeCenterX = eye.left + eye.width / 2;
    const eyeCenterY = eye.top + eye.height / 2;

    const deltaX = mouseX - eyeCenterX;
    const deltaY = mouseY - eyeCenterY;
    const distance = Math.min(Math.sqrt(deltaX ** 2 + deltaY ** 2), maxDistance);

    const angle = Math.atan2(deltaY, deltaX);
    const x = Math.cos(angle) * distance;
    const y = Math.sin(angle) * distance;

    return { x, y };
  };

  const pupilPosition = calculatePupilPosition();

  return (
    <div
      ref={eyeRef}
      className="rounded-full flex items-center justify-center transition-all duration-150"
      style={{
        width: `${size}px`,
        height: isBlinking ? '2px' : `${size}px`,
        backgroundColor: eyeColor,
        overflow: 'hidden',
      }}
    >
      {!isBlinking && (
        <div
          className="rounded-full"
          style={{
            width: `${pupilSize}px`,
            height: `${pupilSize}px`,
            backgroundColor: pupilColor,
            transform: `translate(${pupilPosition.x}px, ${pupilPosition.y}px)`,
            transition: 'transform 0.1s ease-out',
          }}
        />
      )}
    </div>
  );
};

interface LoginPageProps {}

type InfoPanelKey = "privacy" | "terms" | "contact";

const COUNTRY_CODES = ["+91", "+1", "+44", "+61", "+971", "+65"];

const INFO_PANELS: Record<
  InfoPanelKey,
  {
    label: string;
    title: string;
    intro: string;
    icon: typeof ShieldCheck;
    sections: Array<{
      heading: string;
      body: string[];
    }>;
  }
> = {
  privacy: {
    label: "Privacy Policy",
    title: "Urban Sentinel Privacy Policy",
    intro:
      "This page explains what information Urban Sentinel collects, why it is collected, and how it is used to support account access, incident reporting, and platform safety.",
    icon: ShieldCheck,
    sections: [
      {
        heading: "Information We Collect",
        body: [
          "We may collect account details such as your name, email address, phone number, login credentials, and profile information you provide when registering or signing in.",
          "When you submit complaints, reports, or media, we may store descriptions, uploaded files, timestamps, approximate location details, and device or browser information needed to process the submission.",
        ],
      },
      {
        heading: "How We Use Information",
        body: [
          "We use your information to authenticate your account, review reports, manage dashboards, notify you about case activity, and improve the reliability and security of Urban Sentinel services.",
          "Operational logs and analytics may be used to detect misuse, troubleshoot errors, and measure platform performance.",
        ],
      },
      {
        heading: "Sharing and Protection",
        body: [
          "We do not sell your personal information. Data may be shared with authorized administrators, support personnel, service providers, or public safety workflows only when required to operate the platform or respond to lawful requests.",
          "We apply reasonable technical and organizational safeguards, but no online system can guarantee absolute security.",
        ],
      },
      {
        heading: "Your Choices",
        body: [
          "You may request updates to your account information, ask questions about stored data, or contact us regarding privacy concerns using the contact details below.",
          "By continuing to use Urban Sentinel, you acknowledge this privacy notice and the data practices required to deliver the service.",
        ],
      },
    ],
  },
  terms: {
    label: "Terms of Service",
    title: "Urban Sentinel Terms of Service",
    intro:
      "These terms describe the basic rules for using Urban Sentinel, including acceptable use, account responsibilities, and service limitations.",
    icon: FileText,
    sections: [
      {
        heading: "Using the Platform",
        body: [
          "Urban Sentinel is intended for lawful access to monitoring tools, reporting workflows, and related account features. You agree to provide accurate information and use the platform only for legitimate civic, safety, or administrative purposes.",
          "You must not attempt to disrupt the service, access unauthorized data, upload harmful content, or misuse reports in a misleading, fraudulent, or abusive way.",
        ],
      },
      {
        heading: "Accounts and Responsibility",
        body: [
          "You are responsible for protecting your login credentials and for activity that occurs under your account unless unauthorized use is reported promptly.",
          "We may suspend or restrict accounts that violate these terms, threaten platform integrity, or create safety, legal, or operational risk.",
        ],
      },
      {
        heading: "Content and Availability",
        body: [
          "You retain responsibility for the content you submit, including reports, descriptions, and uploaded media. You confirm that you have the right to provide that content and that it does not violate law or third-party rights.",
          "We aim to keep Urban Sentinel available and accurate, but the service may change, pause, or contain interruptions, delays, or errors from time to time.",
        ],
      },
      {
        heading: "Limitations",
        body: [
          "Urban Sentinel is provided on an as-available basis. To the extent permitted by law, we disclaim warranties not expressly stated and limit liability for indirect, incidental, or consequential losses arising from service use.",
          "Continued use of the platform means you accept the current version of these terms.",
        ],
      },
    ],
  },
  contact: {
    label: "Contact",
    title: "Contact Urban Sentinel",
    intro:
      "Use these contact details for support, privacy questions, account help, or partnership inquiries related to the Urban Sentinel platform.",
    icon: MailOpen,
    sections: [
      {
        heading: "Support",
        body: [
          "General support: support@urbansentinel.app",
          "Account recovery and login issues: accounts@urbansentinel.app",
        ],
      },
      {
        heading: "Project Inquiries",
        body: [
          "If you are interested in developing a similar project or wish to collaborate, please contact: grandrakshith@gmail.com with the subject line 'Urban Sentinel Project Inquiry'.",
        ],
      },
      {
        heading: "Privacy and Compliance",
        body: [
          "Privacy requests: privacy@urbansentinel.app",
          "Please include your registered email address, the issue you are facing, and any relevant report or case reference so the team can respond faster.",
        ],
      },
      {
        heading: "Response Expectations",
        body: [
          "We aim to acknowledge most support requests within 2 business days. Urgent safety matters should be escalated through the appropriate emergency or local authority channels rather than waiting for email support.",
          "For product feedback, feature requests, or institutional partnerships, you can also reach us at hello@urbansentinel.app.",
        ],
      },
    ],
  },
};

function parseSavedPhone(rawCountryCode?: string, rawPhone?: string, rawPhoneWithCode?: string) {
  const directCode = String(rawCountryCode || "").trim() || "+91";
  const combined = String(rawPhoneWithCode || "").trim();
  if (combined) {
    const combinedDigits = combined.replace(/\D/g, "");
    const countryDigits = directCode.replace(/\D/g, "");

    // Some older saved records stored only the local phone number in phoneWithCode.
    // If the value is already 10 digits (or shorter), preserve it as-is instead of
    // stripping a country code prefix from the front.
    if (combinedDigits && combinedDigits.length <= 10) {
      return { countryCode: directCode, phone: combinedDigits };
    }

    if (combinedDigits && countryDigits && !combinedDigits.startsWith(countryDigits)) {
      return { countryCode: directCode, phone: combinedDigits };
    }

    const normalized = combined.startsWith("+") ? combined : `+${combined}`;
    const matchedCode =
      [...COUNTRY_CODES]
        .sort((a, b) => b.length - a.length)
        .find((code) => normalized.startsWith(code)) || directCode;
    const phone = normalized.slice(matchedCode.length).replace(/\D/g, "");
    if (phone) {
      return { countryCode: matchedCode, phone };
    }
  }

  const directPhone = String(rawPhone || "").trim().replace(/\D/g, "");
  if (directPhone) {
    return { countryCode: directCode, phone: directPhone };
  }

  return { countryCode: directCode, phone: "" };
}

function LoginPage(props: LoginPageProps) {
  const navigate = useNavigate();
  const emailInputRef = useRef<HTMLInputElement>(null);
  const passwordInputRef = useRef<HTMLInputElement>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [loginMethod, setLoginMethod] = useState<"email" | "phone">("email");
  const [email, setEmail] = useState("");
  const [countryCode, setCountryCode] = useState("+91");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [mouseX, setMouseX] = useState<number>(0);
  const [mouseY, setMouseY] = useState<number>(0);
  const [isPurpleBlinking, setIsPurpleBlinking] = useState(false);
  const [isBlackBlinking, setIsBlackBlinking] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isLookingAtEachOther, setIsLookingAtEachOther] = useState(false);
  const [isPurplePeeking, setIsPurplePeeking] = useState(false);
  const [showSavedLogin, setShowSavedLogin] = useState(false);
  const [savedLogin, setSavedLogin] = useState<{
    identifier: string;
    email?: string;
    countryCode?: string;
    phone?: string;
    phoneWithCode?: string;
    password?: string;
  } | null>(null);
  const [googleEnabled, setGoogleEnabled] = useState(false);
  const [activeInfoPanel, setActiveInfoPanel] = useState<InfoPanelKey | null>(null);
  const purpleRef = useRef<HTMLDivElement>(null);
  const blackRef = useRef<HTMLDivElement>(null);
  const yellowRef = useRef<HTMLDivElement>(null);
  const orangeRef = useRef<HTMLDivElement>(null);
  const phoneInputRef = useRef<HTMLInputElement>(null);
  const [emailFieldArmed, setEmailFieldArmed] = useState(false);
  const [phoneFieldArmed, setPhoneFieldArmed] = useState(false);
  const [passwordFieldArmed, setPasswordFieldArmed] = useState(false);

  useEffect(() => {
    const clearFields = () => {
      setEmail("");
      setPhone("");
      setPassword("");
      if (emailInputRef.current) {
        emailInputRef.current.value = "";
      }
      if (phoneInputRef.current) {
        phoneInputRef.current.value = "";
      }
      if (passwordInputRef.current) {
        passwordInputRef.current.value = "";
      }
    };

    clearFields();
    const timer = window.setTimeout(clearFields, 120);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    try {
      const raw = localStorage.getItem("rememberedLoginProfile");
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (parsed?.identifier) {
        const parsedPhone = parseSavedPhone(parsed.countryCode, parsed.phone, parsed.phoneWithCode);
        const sanitized = {
          identifier: String(parsed.identifier),
          email: parsed.email ? String(parsed.email) : "",
          countryCode: parsedPhone.countryCode,
          phone: parsedPhone.phone,
          phoneWithCode:
            parsed.phoneWithCode
              ? String(parsed.phoneWithCode)
              : parsedPhone.phone
                ? `${parsedPhone.countryCode}${parsedPhone.phone}`
                : "",
          password: parsed.password ? String(parsed.password) : "",
        };
        setSavedLogin({
          ...sanitized,
        });
        localStorage.setItem(
          "rememberedLoginProfile",
          JSON.stringify({
            ...parsed,
            ...sanitized,
          })
        );
      }
    } catch {
      setSavedLogin(null);
    }
  }, []);

  // Handle Google OAuth callback
  useEffect(() => {
    const fetchConfig = async () => {
      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 1200);
      try {
        const res = await fetch(apiUrl("/auth/config"), { signal: controller.signal });
        const json = await res.json();
        setGoogleEnabled(Boolean(json?.google_oauth_enabled));
      } catch {
        setGoogleEnabled(false);
      } finally {
        window.clearTimeout(timeoutId);
      }
    };

    fetchConfig();
  }, []);

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const userParam = urlParams.get('user');
    const accessToken = urlParams.get('access_token') || urlParams.get('token');
    
    if (userParam) {
      try {
        const user = JSON.parse(userParam);
        setAuthSession({ user, token: accessToken || "" });
        localStorage.setItem("rememberedIdentifier", user.email);
        window.history.replaceState({}, document.title, window.location.pathname);
        navigate("/home", { replace: true });
      } catch (error) {
        console.error("Error parsing OAuth callback:", error);
        setError("Google login failed");
      }
    }
  }, [navigate]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMouseX(e.clientX);
      setMouseY(e.clientY);
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  useEffect(() => {
    if (!activeInfoPanel) return;

    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setActiveInfoPanel(null);
      }
    };

    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [activeInfoPanel]);

  // Blinking effects...
  useEffect(() => {
    const getRandomBlinkInterval = () => Math.random() * 4000 + 3000;

    const scheduleBlink = () => {
      const blinkTimeout = setTimeout(() => {
        setIsPurpleBlinking(true);
        setTimeout(() => {
          setIsPurpleBlinking(false);
          scheduleBlink();
        }, 150);
      }, getRandomBlinkInterval());
      return blinkTimeout;
    };

    const timeout = scheduleBlink();
    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    const getRandomBlinkInterval = () => Math.random() * 4000 + 3000;

    const scheduleBlink = () => {
      const blinkTimeout = setTimeout(() => {
        setIsBlackBlinking(true);
        setTimeout(() => {
          setIsBlackBlinking(false);
          scheduleBlink();
        }, 150);
      }, getRandomBlinkInterval());
      return blinkTimeout;
    };

    const timeout = scheduleBlink();
    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    if (isTyping) {
      setIsLookingAtEachOther(true);
      const timer = setTimeout(() => {
        setIsLookingAtEachOther(false);
      }, 800);
      return () => clearTimeout(timer);
    } else {
      setIsLookingAtEachOther(false);
    }
  }, [isTyping]);

  useEffect(() => {
    if (password.length > 0 && showPassword) {
      const schedulePeek = () => {
        const peekInterval = setTimeout(() => {
          setIsPurplePeeking(true);
          setTimeout(() => {
            setIsPurplePeeking(false);
          }, 800);
        }, Math.random() * 3000 + 2000);
        return peekInterval;
      };

      const firstPeek = schedulePeek();
      return () => clearTimeout(firstPeek);
    } else {
      setIsPurplePeeking(false);
    }
  }, [password, showPassword, isPurplePeeking]);

  const calculatePosition = (ref: React.RefObject<HTMLDivElement | null>) => {
    if (!ref.current) return { faceX: 0, faceY: 0, bodySkew: 0 };

    const rect = ref.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 3;

    const deltaX = mouseX - centerX;
    const deltaY = mouseY - centerY;

    const faceX = Math.max(-15, Math.min(15, deltaX / 20));
    const faceY = Math.max(-10, Math.min(10, deltaY / 30));
    const bodySkew = Math.max(-6, Math.min(6, -deltaX / 120));

    return { faceX, faceY, bodySkew };
  };
  const handleGoogleLogin = () => {
    window.location.href = apiUrl("/auth/google");
  };
  const purplePos = calculatePosition(purpleRef);
  const blackPos = calculatePosition(blackRef);
  const yellowPos = calculatePosition(yellowRef);
  const orangePos = calculatePosition(orangeRef);
  const hasSavedOption =
    loginMethod === "email"
      ? Boolean(savedLogin?.email || savedLogin?.identifier)
      : Boolean(savedLogin?.phone || savedLogin?.phoneWithCode);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (loginMethod !== "email") {
      setError("Use your registered email and password.");
      return;
    }

    setIsLoading(true);

    try {
      const payload = await authApi.login({
        email: email.trim(),
        password,
      });

      if (payload?.status !== "success") {
        throw new Error(payload?.message || "Login failed");
      }

      setAuthSession({
        user: payload.user,
        token: payload.access_token || payload.token || "",
      });
      void prefetchDashboardBootstrap();

      if (rememberMe) {
        localStorage.setItem("rememberedIdentifier", email.trim());
        localStorage.setItem(
          "rememberedLoginProfile",
          JSON.stringify({
            identifier: email.trim(),
            email: payload.user?.email || email.trim(),
            countryCode,
            phone: loginMethod === "phone" ? phone.trim() : "",
            phoneWithCode: loginMethod === "phone" ? `${countryCode}${phone.trim()}` : payload.user?.phone || "",
            password,
            source: "login",
            savedAt: new Date().toISOString(),
          })
        );
      } else {
        localStorage.removeItem("rememberedIdentifier");
        localStorage.removeItem("rememberedLoginProfile");
      }

      navigate("/home", { replace: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Invalid email or password";
      setError(message);
      console.error("Login error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const activePanel = activeInfoPanel ? INFO_PANELS[activeInfoPanel] : null;

  return (
    <>
      <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left Content Section */}
      <div className="relative hidden lg:flex flex-col justify-between bg-gradient-to-br from-primary/90 via-primary to-primary/80 p-12 text-primary-foreground">
        <div className="relative z-20">
          <div className="flex items-center gap-2 text-lg font-semibold">
            <div className="size-8 rounded-lg bg-primary-foreground/10 backdrop-blur-sm flex items-center justify-center">
              <Sparkles className="size-4" />
            </div>
            <span>Urban Sentinel</span>
          </div>
        </div>

        <div className="relative z-20 flex items-end justify-center h-[500px]">
          {/* Cartoon Characters */}
          <div className="relative" style={{ width: '550px', height: '400px' }}>
            {/* Purple tall rectangle character - Back layer */}
            <div 
              ref={purpleRef}
              className="absolute bottom-0 transition-all duration-700 ease-in-out"
              style={{
                left: '70px',
                width: '180px',
                height: (isTyping || (password.length > 0 && !showPassword)) ? '440px' : '400px',
                backgroundColor: '#6C3FF5',
                borderRadius: '10px 10px 0 0',
                zIndex: 1,
                transform: (password.length > 0 && showPassword)
                  ? `skewX(0deg)`
                  : (isTyping || (password.length > 0 && !showPassword))
                    ? `skewX(${(purplePos.bodySkew || 0) - 12}deg) translateX(40px)` 
                    : `skewX(${purplePos.bodySkew || 0}deg)`,
                transformOrigin: 'bottom center',
              }}
            >
              {/* Eyes */}
              <div 
                className="absolute flex gap-8 transition-all duration-700 ease-in-out"
                style={{
                  left: (password.length > 0 && showPassword) ? `${20}px` : isLookingAtEachOther ? `${55}px` : `${45 + purplePos.faceX}px`,
                  top: (password.length > 0 && showPassword) ? `${35}px` : isLookingAtEachOther ? `${65}px` : `${40 + purplePos.faceY}px`,
                }}
              >
                <EyeBall 
                  size={18} 
                  pupilSize={7} 
                  maxDistance={5} 
                  eyeColor="white" 
                  pupilColor="#2D2D2D" 
                  isBlinking={isPurpleBlinking}
                  forceLookX={(password.length > 0 && showPassword) ? (isPurplePeeking ? 4 : -4) : isLookingAtEachOther ? 3 : undefined}
                  forceLookY={(password.length > 0 && showPassword) ? (isPurplePeeking ? 5 : -4) : isLookingAtEachOther ? 4 : undefined}
                />
                <EyeBall 
                  size={18} 
                  pupilSize={7} 
                  maxDistance={5} 
                  eyeColor="white" 
                  pupilColor="#2D2D2D" 
                  isBlinking={isPurpleBlinking}
                  forceLookX={(password.length > 0 && showPassword) ? (isPurplePeeking ? 4 : -4) : isLookingAtEachOther ? 3 : undefined}
                  forceLookY={(password.length > 0 && showPassword) ? (isPurplePeeking ? 5 : -4) : isLookingAtEachOther ? 4 : undefined}
                />
              </div>
            </div>

            {/* Black tall rectangle character - Middle layer */}
            <div 
              ref={blackRef}
              className="absolute bottom-0 transition-all duration-700 ease-in-out"
              style={{
                left: '240px',
                width: '120px',
                height: '310px',
                backgroundColor: '#2D2D2D',
                borderRadius: '8px 8px 0 0',
                zIndex: 2,
                transform: (password.length > 0 && showPassword)
                  ? `skewX(0deg)`
                  : isLookingAtEachOther
                    ? `skewX(${(blackPos.bodySkew || 0) * 1.5 + 10}deg) translateX(20px)`
                    : (isTyping || (password.length > 0 && !showPassword))
                      ? `skewX(${(blackPos.bodySkew || 0) * 1.5}deg)` 
                      : `skewX(${blackPos.bodySkew || 0}deg)`,
                transformOrigin: 'bottom center',
              }}
            >
              {/* Eyes */}
              <div 
                className="absolute flex gap-6 transition-all duration-700 ease-in-out"
                style={{
                  left: (password.length > 0 && showPassword) ? `${10}px` : isLookingAtEachOther ? `${32}px` : `${26 + blackPos.faceX}px`,
                  top: (password.length > 0 && showPassword) ? `${28}px` : isLookingAtEachOther ? `${12}px` : `${32 + blackPos.faceY}px`,
                }}
              >
                <EyeBall 
                  size={16} 
                  pupilSize={6} 
                  maxDistance={4} 
                  eyeColor="white" 
                  pupilColor="#2D2D2D" 
                  isBlinking={isBlackBlinking}
                  forceLookX={(password.length > 0 && showPassword) ? -4 : isLookingAtEachOther ? 0 : undefined}
                  forceLookY={(password.length > 0 && showPassword) ? -4 : isLookingAtEachOther ? -4 : undefined}
                />
                <EyeBall 
                  size={16} 
                  pupilSize={6} 
                  maxDistance={4} 
                  eyeColor="white" 
                  pupilColor="#2D2D2D" 
                  isBlinking={isBlackBlinking}
                  forceLookX={(password.length > 0 && showPassword) ? -4 : isLookingAtEachOther ? 0 : undefined}
                  forceLookY={(password.length > 0 && showPassword) ? -4 : isLookingAtEachOther ? -4 : undefined}
                />
              </div>
            </div>

            {/* Orange semi-circle character - Front left */}
            <div 
              ref={orangeRef}
              className="absolute bottom-0 transition-all duration-700 ease-in-out"
              style={{
                left: '0px',
                width: '240px',
                height: '200px',
                zIndex: 3,
                backgroundColor: '#FF9B6B',
                borderRadius: '120px 120px 0 0',
                transform: (password.length > 0 && showPassword) ? `skewX(0deg)` : `skewX(${orangePos.bodySkew || 0}deg)`,
                transformOrigin: 'bottom center',
              }}
            >
              {/* Eyes - just pupils, no white */}
              <div 
                className="absolute flex gap-8 transition-all duration-200 ease-out"
                style={{
                  left: (password.length > 0 && showPassword) ? `${50}px` : `${82 + (orangePos.faceX || 0)}px`,
                  top: (password.length > 0 && showPassword) ? `${85}px` : `${90 + (orangePos.faceY || 0)}px`,
                }}
              >
                <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={(password.length > 0 && showPassword) ? -5 : undefined} forceLookY={(password.length > 0 && showPassword) ? -4 : undefined} />
                <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={(password.length > 0 && showPassword) ? -5 : undefined} forceLookY={(password.length > 0 && showPassword) ? -4 : undefined} />
              </div>
            </div>

            {/* Yellow tall rectangle character - Front right */}
            <div 
              ref={yellowRef}
              className="absolute bottom-0 transition-all duration-700 ease-in-out"
              style={{
                left: '310px',
                width: '140px',
                height: '230px',
                backgroundColor: '#E8D754',
                borderRadius: '70px 70px 0 0',
                zIndex: 4,
                transform: (password.length > 0 && showPassword) ? `skewX(0deg)` : `skewX(${yellowPos.bodySkew || 0}deg)`,
                transformOrigin: 'bottom center',
              }}
            >
              {/* Eyes - just pupils, no white */}
              <div 
                className="absolute flex gap-6 transition-all duration-200 ease-out"
                style={{
                  left: (password.length > 0 && showPassword) ? `${20}px` : `${52 + (yellowPos.faceX || 0)}px`,
                  top: (password.length > 0 && showPassword) ? `${35}px` : `${40 + (yellowPos.faceY || 0)}px`,
                }}
              >
                <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={(password.length > 0 && showPassword) ? -5 : undefined} forceLookY={(password.length > 0 && showPassword) ? -4 : undefined} />
                <Pupil size={12} maxDistance={5} pupilColor="#2D2D2D" forceLookX={(password.length > 0 && showPassword) ? -5 : undefined} forceLookY={(password.length > 0 && showPassword) ? -4 : undefined} />
              </div>
              {/* Horizontal line for mouth */}
              <div 
                className="absolute w-20 h-[4px] bg-[#2D2D2D] rounded-full transition-all duration-200 ease-out"
                style={{
                  left: (password.length > 0 && showPassword) ? `${10}px` : `${40 + (yellowPos.faceX || 0)}px`,
                  top: (password.length > 0 && showPassword) ? `${88}px` : `${88 + (yellowPos.faceY || 0)}px`,
                }}
              />
            </div>
          </div>
        </div>

        <div className="relative z-20 flex items-center gap-8 text-sm text-primary-foreground/60">
          {(["privacy", "terms", "contact"] as InfoPanelKey[]).map((panelKey) => (
            <button
              key={panelKey}
              type="button"
              onClick={() => setActiveInfoPanel(panelKey)}
              className="transition-colors hover:text-primary-foreground"
            >
              {INFO_PANELS[panelKey].label}
            </button>
          ))}
        </div>

        {/* Decorative elements */}
        <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:20px_20px]" />
        <div className="absolute top-1/4 right-1/4 size-64 bg-primary-foreground/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/4 size-96 bg-primary-foreground/5 rounded-full blur-3xl" />
      </div>

      {/* Right Login Section */}
      <div className="flex items-center justify-center p-8 bg-background">
        <div className="w-full max-w-[420px]">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-2 text-lg font-semibold mb-12">
            <div className="size-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <Sparkles className="size-4 text-primary" />
            </div>
            <span>Urban Sentinel</span>
          </div>

          {/* Header */}
          <div className="text-center mb-10">
            <h1 className="text-3xl font-bold tracking-tight mb-2">Welcome back!</h1>
            <p className="text-muted-foreground text-sm">Please enter your details</p>
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-5" autoComplete="off">
            <div className="space-y-3">
              <Label className="text-sm font-medium">Choose login method</Label>
              <div className="grid grid-cols-2 gap-3 rounded-2xl bg-primary/5 p-1.5">
                <button
                  type="button"
                  onClick={() => {
                    setLoginMethod("email");
                    setShowSavedLogin(false);
                  }}
                  className={cn(
                    "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold transition-all",
                    loginMethod === "email"
                      ? "bg-primary text-primary-foreground shadow-[0_10px_24px_rgba(15,23,42,0.18)]"
                      : "text-muted-foreground hover:bg-background hover:text-foreground"
                  )}
                >
                  <Mail className="size-4" />
                  Email
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setLoginMethod("phone");
                    setShowSavedLogin(false);
                  }}
                  className={cn(
                    "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold transition-all",
                    loginMethod === "phone"
                      ? "bg-primary text-primary-foreground shadow-[0_10px_24px_rgba(15,23,42,0.18)]"
                      : "text-muted-foreground hover:bg-background hover:text-foreground"
                  )}
                >
                  <Phone className="size-4" />
                  Phone
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor={loginMethod === "email" ? "email" : "phone"} className="text-sm font-medium">
                {loginMethod === "email" ? "Email" : "Phone Number"}
              </Label>
              <div className="relative">
                {loginMethod === "email" ? (
                  <Input
                    ref={emailInputRef}
                    id="email"
                    type="email"
                    name="login_email_input"
                    placeholder="Enter your email"
                    value={email}
                    autoComplete="off"
                    readOnly={!emailFieldArmed}
                    onChange={(e) => setEmail(e.target.value)}
                    onFocus={() => {
                      setEmailFieldArmed(true);
                      setIsTyping(true);
                      if (hasSavedOption) {
                        setShowSavedLogin(true);
                      }
                    }}
                    onBlur={() => {
                      setIsTyping(false);
                      window.setTimeout(() => setShowSavedLogin(false), 150);
                    }}
                    required={loginMethod === "email"}
                    className="h-12 bg-background border-border/60 text-foreground placeholder:text-muted-foreground/60 focus:border-primary"
                  />
                ) : (
                  <div className="grid grid-cols-[96px_minmax(0,1fr)] gap-3">
                    <select
                      value={countryCode}
                      onChange={(event) => setCountryCode(event.target.value)}
                      className="h-12 rounded-xl border border-border/60 bg-background px-3 text-sm font-medium text-foreground outline-none transition-colors focus:border-primary"
                    >
                      {COUNTRY_CODES.map((code) => (
                        <option key={code} value={code}>
                          {code}
                        </option>
                      ))}
                    </select>
                    <Input
                      id="phone"
                      type="tel"
                      name="login_phone_input"
                      placeholder="Enter your phone number"
                      ref={phoneInputRef}
                      value={phone}
                      autoComplete="off"
                      readOnly={!phoneFieldArmed}
                      onChange={(e) => setPhone(e.target.value.replace(/\D/g, ""))}
                      onFocus={() => {
                        setPhoneFieldArmed(true);
                        setIsTyping(true);
                        if (hasSavedOption) {
                          setShowSavedLogin(true);
                        }
                      }}
                      onBlur={() => {
                        setIsTyping(false);
                        window.setTimeout(() => setShowSavedLogin(false), 150);
                      }}
                      required={loginMethod === "phone"}
                      className="h-12 bg-background border-border/60 text-foreground placeholder:text-muted-foreground/60 focus:border-primary"
                    />
                  </div>
                )}
                {showSavedLogin && savedLogin && hasSavedOption ? (
                  <div className="mt-3 overflow-hidden rounded-2xl border border-border/70 bg-card shadow-[0_12px_24px_rgba(15,23,42,0.08)]">
                    <button
                      type="button"
                      onClick={() => {
                        if (loginMethod === "email") {
                          setEmail(savedLogin.email || savedLogin.identifier);
                        } else {
                          setCountryCode(savedLogin.countryCode || "+91");
                          setPhone(savedLogin.phone || "");
                        }
                        setPassword(savedLogin.password || "");
                        setShowSavedLogin(false);
                        window.setTimeout(() => passwordInputRef.current?.focus(), 0);
                      }}
                      className="w-full px-4 py-3 text-left transition-colors hover:bg-accent/40"
                    >
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                        Saved account
                      </p>
                      <p className="mt-1 truncate text-sm font-medium text-foreground">
                        {loginMethod === "email"
                          ? savedLogin.email || savedLogin.identifier
                          : savedLogin.phoneWithCode || `${savedLogin.countryCode || "+91"}${savedLogin.phone || ""}`}
                      </p>
                    </button>
                  </div>
                ) : null}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-sm font-medium">Password</Label>
              <div className="relative">
                <Input
                  ref={passwordInputRef}
                  id="password"
                  type={showPassword ? "text" : "password"}
                  name="login_password_input"
                  placeholder="Password"
                  value={password}
                  autoComplete="off"
                  readOnly={!passwordFieldArmed}
                  onChange={(e) => setPassword(e.target.value)}
                  onFocus={() => setPasswordFieldArmed(true)}
                  required
                  className="h-12 pr-10 bg-background border-border/60 text-foreground placeholder:text-muted-foreground/60 focus:border-primary"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? (
                    <EyeOff className="size-5" />
                  ) : (
                    <Eye className="size-5" />
                  )}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Checkbox id="remember" checked={rememberMe} onCheckedChange={(checked) => setRememberMe(checked as boolean)} />
                <Label
                  htmlFor="remember"
                  className="text-sm font-normal cursor-pointer"
                >
                  Remember for 30 days
                </Label>
              </div>
              <a
                href="/forgot-password"
                className="text-sm text-primary hover:underline font-medium"
              >
                Forgot password?
              </a>
            </div>

            {error && (
              <div className="p-3 text-sm text-red-400 bg-red-950/20 border border-red-900/30 rounded-lg">
                {error}
              </div>
            )}

            <RippleButton
              type="submit"
              className="w-full h-12 text-base font-medium"
              disabled={isLoading}
            >
              {isLoading ? "Signing in..." : "Log in"}
            </RippleButton>
          </form>

          {/* Sign Up Link */}
          <div className="text-center text-sm text-muted-foreground mt-6">
            Don't have an account?{" "}
            <a href="/register" className="text-foreground font-medium hover:underline">
              Register here
            </a>
          </div>

          <div className="lg:hidden mt-8 flex flex-wrap items-center justify-center gap-x-5 gap-y-3 text-sm text-muted-foreground">
            {(["privacy", "terms", "contact"] as InfoPanelKey[]).map((panelKey) => (
              <button
                key={panelKey}
                type="button"
                onClick={() => setActiveInfoPanel(panelKey)}
                className="transition-colors hover:text-foreground"
              >
                {INFO_PANELS[panelKey].label}
              </button>
            ))}
          </div>
        </div>
      </div>

      </div>

      {activePanel ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 p-4 backdrop-blur-md sm:p-6"
          onClick={() => setActiveInfoPanel(null)}
        >
          <div
            className="relative w-full max-w-4xl overflow-hidden rounded-[32px] border border-white/20 bg-white shadow-[0_32px_80px_rgba(15,23,42,0.34)]"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 z-10 border-b border-slate-200/80 bg-white/92 backdrop-blur-xl">
                <div className="flex items-start justify-between gap-6 px-6 py-5 sm:px-8">
                  <div className="flex items-start gap-4">
                    <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-[0_14px_28px_rgba(15,23,42,0.16)]">
                      <activePanel.icon className="size-5" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">
                        Urban Sentinel
                      </p>
                      <h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">
                        {activePanel.title}
                      </h2>
                      <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
                        {activePanel.intro}
                      </p>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => setActiveInfoPanel(null)}
                    className="inline-flex size-10 shrink-0 items-center justify-center rounded-full border border-slate-200 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-950"
                    aria-label="Close information panel"
                  >
                    <X className="size-5" />
                  </button>
                </div>
              </div>

              <div className="bg-[linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] px-6 py-6 sm:px-8 sm:py-8">
                {/* Sample legal/support content notice removed as requested */}

                <div className="space-y-6">
                  {activePanel.sections.map((section) => (
                    <section
                      key={section.heading}
                      className="rounded-3xl border border-slate-200 bg-white p-5 shadow-[0_12px_32px_rgba(15,23,42,0.06)]"
                    >
                      <h3 className="text-lg font-semibold text-slate-950">{section.heading}</h3>
                      <div className="mt-3 space-y-3">
                        {section.body.map((paragraph) => (
                          <p key={paragraph} className="text-sm leading-7 text-slate-600">
                            {paragraph}
                          </p>
                        ))}
                      </div>
                    </section>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}

export default LoginPage;
