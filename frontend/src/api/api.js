const API_BASE = "http://localhost:8000";

export function saveAuth(token, user) {
  localStorage.setItem("token", token);
  localStorage.setItem("user", JSON.stringify(user));
}

export function getToken() {
  return localStorage.getItem("token");
}

export function getUser() {
  const user = localStorage.getItem("user");
  return user ? JSON.parse(user) : null;
}

export function clearAuth() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
}

async function request(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });
  } catch {
    try {
      const altBase = API_BASE.includes("localhost") ? "http://127.0.0.1:8000" : "http://localhost:8000";
      response = await fetch(`${altBase}${path}`, {
        ...options,
        headers,
      });
    } catch {
      throw new Error(
        "Cannot connect to server. Make sure the backend is running on http://localhost:8000"
      );
    }
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = data.detail || "Something went wrong";
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }

  return data;
}

export function signup(payload) {
  return request("/api/signup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function login(payload) {
  return request("/api/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchProfile() {
  return request("/api/me");
}

export function fetchHealthProfile() {
  return request("/api/health-profile");
}

export function saveHealthProfile(payload) {
  return request("/api/health-profile", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function navigateAfterAuth(navigate) {
  try {
    await fetchHealthProfile();
    navigate("/dashboard");
  } catch {
    navigate("/health-profile");
  }
}

export function searchFoods(query) {
  return request(`/api/foods/search?q=${encodeURIComponent(query)}&limit=15`);
}

export function fetchDiaryEntries(date) {
  return request(`/api/diary?date=${date}`);
}

export function addDiaryEntry(payload) {
  return request("/api/diary", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteDiaryEntry(id) {
  return request(`/api/diary/${id}`, {
    method: "DELETE",
  });
}

export function fetchLabResults() {
  return request("/api/lab-results");
}

export function saveLabResults(payload) {
  return request("/api/lab-results", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

