import React, { useState } from "react";
import { useGoogleLogin } from "@react-oauth/google";
import { Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";
import PageLoader from "../components/PageLoader";

const Login = () => {
  const { user, loading, login } = useAuth();
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const navigate = useNavigate();

  const handleGoogleLogin = useGoogleLogin({
    flow: "auth-code",
    scope: "https://www.googleapis.com/auth/calendar.events",
    onSuccess: async (codeResponse) => {
      if (isLoggingIn) return;
      setIsLoggingIn(true);
      try {
        const res = await fetch(
          `${import.meta.env.VITE_BACKEND_URL}/auth/google`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ code: codeResponse.code }),
          },
        );
        if (!res.ok) {
          throw new Error("Auth failed.");
        }
        const data = await res.json();
        login(data.access_token);
        navigate("/", { replace: true });
      } catch (err) {
        setIsLoggingIn(false);
        toast.error("Login error.");
      }
    },
    onError: () => toast.error("Login failed"),
  });

  if (loading) return <PageLoader />;

  if (user) {
    return <Navigate to="/" replace />;
  }
  return (
    <div style={{ height: "100vh", display: "grid", placeItems: "center" }}>
      {isLoggingIn ? (
        <PageLoader />
      ) : (
        <button
          onClick={() => handleGoogleLogin()}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            padding: "10px 20px",
            fontSize: "16px",
            cursor: "pointer",
            borderRadius: "4px",
            border: "1px solid #dadce0",
            backgroundColor: "#fff",
            fontWeight: "500",
          }}
        >
          <img
            src="https://www.gstatic.com/images/branding/product/1x/gsa_512dp.png"
            width="20"
            alt="google"
          />
          Sign in with Google
        </button>
      )}
    </div>
  );
};

export default Login;
