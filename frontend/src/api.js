import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

export async function signup(email, password, fullName) {
  const response = await api.post("/auth/signup", {
    email,
    password,
    full_name: fullName || null,
  });
  return response.data;
}

export async function login(email, password) {
  const response = await api.post("/auth/login", { email, password });
  return response.data;
}

export async function refresh(refreshToken) {
  const response = await api.post("/auth/refresh", { refresh_token: refreshToken });
  return response.data;
}

export async function me(token) {
  const response = await api.get("/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
}

export async function analyze(token, imageBase64 = null, questionnaire = null) {
  const response = await api.post(
    "/analyze",
    {
      image_base64: imageBase64 || "demo-image",
      questionnaire: questionnaire || {
        skin_feel: "oily",
        routine: "basic",
        concerns: ["acne"],
      },
    },
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );
  return response.data;
}

export async function recommend(token, skinType, conditions) {
  const response = await api.post(
    "/recommend",
    { skin_type: skinType, conditions },
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );
  return response.data;
}

export async function getProfile(token, userId) {
  const response = await api.get(`/profile/${userId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
}
