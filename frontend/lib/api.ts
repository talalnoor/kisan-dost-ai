const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function setToken(token: string) {
  localStorage.setItem("access_token", token);
}

export function clearToken() {
  localStorage.removeItem("access_token");
}

export async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new Error(
      `Cannot reach the server at ${API_URL}. Check that the backend is running and NEXT_PUBLIC_API_URL is correct.`
    );
  }

  let data: any = null;
  try {
    data = await response.json();
  } catch {
    // Non-JSON response (e.g. a 502 page from the host)
  }

  if (!response.ok) {
    const detail = data?.detail;
    let message: string;
    if (typeof detail === "string") message = detail;
    else if (detail?.message) message = detail.message;
    else if (Array.isArray(detail))
      message = detail.map((d: any) => `${(d.loc || []).join(".")}: ${d.msg}`).join("; ");
    else message = `Server error (${response.status})`;
    throw new Error(message);
  }

  return data;
}