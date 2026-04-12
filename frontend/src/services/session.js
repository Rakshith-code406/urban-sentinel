let memoryToken = null;
let memoryUser = null;

function readStorage(key) {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(key);
}

export function getAccessToken() {
  if (memoryToken !== null) return memoryToken;
  memoryToken = readStorage("access_token") || readStorage("token") || "";
  return memoryToken;
}

export function getStoredUser() {
  if (memoryUser !== null) return memoryUser;
  const raw = readStorage("user");
  memoryUser = raw || "";
  return memoryUser;
}

export function setAuthSession({ token = "", user = null } = {}) {
  memoryToken = token || "";
  memoryUser = typeof user === "string" ? user : user ? JSON.stringify(user) : "";
  if (typeof localStorage === "undefined") return;
  if (memoryToken) {
    localStorage.setItem("access_token", memoryToken);
  } else {
    localStorage.removeItem("access_token");
    localStorage.removeItem("token");
  }
  if (memoryUser) {
    localStorage.setItem("user", memoryUser);
  } else {
    localStorage.removeItem("user");
  }
}

export function clearAuthSession() {
  memoryToken = "";
  memoryUser = "";
  if (typeof localStorage === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

