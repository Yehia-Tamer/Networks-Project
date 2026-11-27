// One fetch wrapper: adds the token, sends the user to /login on a 401.
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const getToken = () => localStorage.getItem("token");
export const setToken = (t) => localStorage.setItem("token", t);
export const clearToken = () => localStorage.removeItem("token");
export { API_URL };

export async function api(path, { method = "GET", body, form = false } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let payload;
  if (body !== undefined) {
    if (form) {
      payload = new URLSearchParams(body); // /auth/login expects form data
      headers["Content-Type"] = "application/x-www-form-urlencoded";
    } else {
      payload = JSON.stringify(body);
      headers["Content-Type"] = "application/json";
    }
  }

  const res = await fetch(`${API_URL}${path}`, { method, headers, body: payload });

  if (res.status === 401 && path !== "/auth/login") {
    clearToken();
    window.location.href = "/login";
    throw new Error("Session expired");
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = typeof data.detail === "string"
        ? data.detail
        : Array.isArray(data.detail) // FastAPI validation errors: [{loc, msg}, ...]
          ? data.detail.map((d) => d.msg.replace(/^Value error, /, "")).join(". ")
          : JSON.stringify(data.detail);
    } catch { /* not JSON */ }
    throw new Error(detail);
  }
  return res.status === 204 ? null : res.json();
}
