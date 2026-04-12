import type { ReactNode } from "react";
import { Suspense, lazy } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { getStoredUser } from "./services/session";

const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const Home = lazy(() => import("./pages/Home"));
const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const Report = lazy(() => import("./pages/Report"));
const TrackComplaint = lazy(() => import("./pages/TrackComplaint"));
const TrackLookup = lazy(() => import("./pages/TrackLookup"));
const Demo = lazy(() => import("./pages/Demo"));
const DemoOne = lazy(() => import("./pages/DemoOne"));

function ProtectedRoute({ children }: { children: ReactNode }) {
  const user = getStoredUser();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <Suspense fallback={<div style={{ minHeight: "100vh", display: "grid", placeItems: "center", background: "#050816", color: "#fff" }}>Loading...</div>}>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route
          path="/home"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />
        <Route
          path="/report"
          element={
            <ProtectedRoute>
              <Report />
            </ProtectedRoute>
          }
        />
        <Route
          path="/track"
          element={
            <ProtectedRoute>
              <TrackLookup />
            </ProtectedRoute>
          }
        />
        <Route
          path="/track/:complaint_number"
          element={
            <ProtectedRoute>
              <TrackComplaint />
            </ProtectedRoute>
          }
        />
        <Route path="/demo" element={<Demo />} />
        <Route path="/demo-one" element={<DemoOne />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Suspense>
  );
}

export default App;
