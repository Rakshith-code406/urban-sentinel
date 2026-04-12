import { useState } from "react";
import { apiUrl } from "../services/apiBase";

export default function AdminLogin() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const login = async () => {
    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);

    const res = await fetch(apiUrl("/admin/session-login"), {
      method: "POST",
      body: form,
      redirect: "manual",
    });

    if (![200, 303].includes(res.status)) return alert("Invalid credentials");

    localStorage.setItem("adminSession", "true");
    alert("Login Successful");
    window.location.href = "/";
  };

  return (
    <div className="login-container">
      <h2>Admin Login</h2>
      <input placeholder="Username" onChange={(e) => setUsername(e.target.value)} />
      <input type="password" placeholder="Password"
        onChange={(e) => setPassword(e.target.value)} />
      <button onClick={login}>Login</button>
    </div>
  );
}
