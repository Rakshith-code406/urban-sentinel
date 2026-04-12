import { API_BASE } from "./apiBase";

async function postJson(path, body) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      throw new Error(data?.detail || data?.message || `Request failed (${res.status})`);
    }

    return data;
  } catch (err) {
    console.error("API ERROR:", err);
    throw err;
  }
}

export async function loginUser(email, password) {
  return postJson("/auth/login", { email, password });
}

export const authApi = {
  register: (data) => postJson("/auth/register", data),
  login: (data) => loginUser(data.email, data.password),
  requestForgotPassword: (data) => postJson("/send-otp", data),
  verifyForgotPassword: (data) => postJson("/verify-otp", data),
  resetForgotPassword: (data) => postJson("/reset-password", data),
};

export { API_BASE };
