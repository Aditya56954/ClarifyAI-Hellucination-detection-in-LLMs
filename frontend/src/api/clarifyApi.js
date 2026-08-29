// frontend/src/api/clarifyApi.js

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://localhost:8000/api/v1";

/*
|--------------------------------------------------------------------------
| Generic API Request
|--------------------------------------------------------------------------
*/

async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem("clarifyai_token");

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  // Add JWT automatically for authenticated requests.
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  let data = null;

  try {
    data = await response.json();
  } catch {
    // Response may not contain JSON.
  }

  if (!response.ok) {
    const message =
      data?.detail ||
      data?.message ||
      `Request failed with status ${response.status}`;

    throw new Error(message);
  }

  return data;
}

/*
|--------------------------------------------------------------------------
| Authentication
|--------------------------------------------------------------------------
*/

/**
 * Register a new user.
 */
export async function registerUser(name, email, password) {
  return apiRequest("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      name,
      email,
      password,
    }),
  });
}

/**
 * Login user.
 *
 * Stores the returned JWT automatically.
 */
export async function loginUser(email, password) {
  const data = await apiRequest("/auth/login", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
    }),
  });

  if (data?.access_token) {
    localStorage.setItem(
      "clarifyai_token",
      data.access_token
    );
  }

  return data;
}

/**
 * Logout current user.
 */
export function logoutUser() {
  localStorage.removeItem("clarifyai_token");
}

/**
 * Check whether the user has a stored JWT.
 */
export function isAuthenticated() {
  return Boolean(
    localStorage.getItem("clarifyai_token")
  );
}

/**
 * Get current authenticated user.
 */
export async function getCurrentUser() {
  return apiRequest("/auth/me", {
    method: "GET",
  });
}

/*
|--------------------------------------------------------------------------
| ClarifyAI Query
|--------------------------------------------------------------------------
*/

/**
 * Send a question to ClarifyAI.
 *
 * Flow:
 *
 * Question
 *   ↓
 * Evidence Retrieval
 *   ↓
 * Answer Generation
 *   ↓
 * Semantic Verification
 *   ↓
 * Discrepancy Detection
 *   ↓
 * Contradiction Detection
 *   ↓
 * Confidence
 *   ↓
 * Final Response
 */
export async function askClarifyAI(question) {
  const cleanedQuestion = question?.trim();

  if (!cleanedQuestion) {
    throw new Error("Please enter a question.");
  }

  if (cleanedQuestion.length < 3) {
    throw new Error(
      "Question must contain at least 3 characters."
    );
  }

  if (cleanedQuestion.length > 2000) {
    throw new Error(
      "Question cannot exceed 2000 characters."
    );
  }

  return apiRequest("/query", {
    method: "POST",
    body: JSON.stringify({
      question: cleanedQuestion,
    }),
  });
}

/*
|--------------------------------------------------------------------------
| Backend Health
|--------------------------------------------------------------------------
*/

/**
 * Check whether the backend is running.
 */
export async function checkBackendHealth() {
  return apiRequest("/health", {
    method: "GET",
  });
}

/*
|--------------------------------------------------------------------------
| Authentication Helpers
|--------------------------------------------------------------------------
*/

/**
 * Get stored JWT.
 */
export function getAuthToken() {
  return localStorage.getItem(
    "clarifyai_token"
  );
}

/**
 * Completely clear authentication state.
 */
export function clearAuth() {
  localStorage.removeItem(
    "clarifyai_token"
  );
}

/*
|--------------------------------------------------------------------------
| Default Export
|--------------------------------------------------------------------------
*/

const clarifyApi = {
  registerUser,
  loginUser,
  logoutUser,
  isAuthenticated,
  getCurrentUser,
  askClarifyAI,
  checkBackendHealth,
  getAuthToken,
  clearAuth,
};

export default clarifyApi;