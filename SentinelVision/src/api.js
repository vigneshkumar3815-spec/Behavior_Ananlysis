const API_BASE = "http://localhost:8002/api";

export const fetchEvents = async () => {
  try {
    const res = await fetch(`${API_BASE}/events`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.events || [];
  } catch (err) {
    console.error("Failed to fetch events", err);
    return [];
  }
};
