// Use environment variable for API URL, fallback to localhost for development
const API_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api"

export const API_BASE_URL = API_URL