const API_URL = "http://localhost:5000/auth";

const login = async (email, password) => {
  const response = await fetch(`${API_URL}/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json();
  return { ok: response.ok, data };
};

const signup = async (email, password, nom, prenom) => {
  const response = await fetch(`${API_URL}/signup`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password, nom, prenom }),
  });
  const data = await response.json();
  return { ok: response.ok, data };
};

export const authService = {
  login,
  signup,
};
