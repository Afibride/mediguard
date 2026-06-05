const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const FALLBACK_API_URL = 'http://localhost:8001';

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, options = {}) {
  const token = localStorage.getItem('mediguard_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const urls = [...new Set([API_URL, FALLBACK_API_URL])];
  let response;
  let lastNetworkError;

  for (const baseUrl of urls) {
    try {
      response = await fetch(`${baseUrl}${path}`, {
        ...options,
        headers,
      });
      if (response.ok || response.status !== 404) break;
    } catch (error) {
      lastNetworkError = error;
    }
  }

  if (!response && lastNetworkError) {
    throw lastNetworkError;
  }

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    throw new ApiError(data?.detail || data?.message || 'API request failed', response.status);
  }

  return { data };
}

const queryString = (params = {}) => {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '' && value !== 'All') {
      search.set(key, value);
    }
  });
  const value = search.toString();
  return value ? `?${value}` : '';
};

export const register = (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) });
export const login = (data) => request('/auth/login', { method: 'POST', body: JSON.stringify(data) });
export const forgotPassword = (data) => request('/auth/forgot-password', { method: 'POST', body: JSON.stringify(data) });
export const resetPassword = (data) => request('/auth/reset-password', { method: 'POST', body: JSON.stringify(data) });
export const getMe = () => request('/auth/me');
export const updateProfile = (data) => request('/auth/me', { method: 'PATCH', body: JSON.stringify(data) });
export const changePassword = (data) => request('/auth/me/change-password', { method: 'POST', body: JSON.stringify(data) });

export const getSymptoms = () => request('/symptoms');
export const predictDisease = (symptoms, context = {}) =>
  request('/predict', { method: 'POST', body: JSON.stringify({ symptoms, ...context }) });
export const normalizeSymptoms = (text) =>
  request('/normalize-symptoms', { method: 'POST', body: JSON.stringify({ text }) });
export const getClarifyQuestions = (current_symptoms, top_diseases = [], already_asked = []) =>
  request('/predict/clarify', { method: 'POST', body: JSON.stringify({ current_symptoms, top_diseases, already_asked }) });
export const submitFeedback = (data) =>
  request('/predict/feedback', { method: 'POST', body: JSON.stringify(data) });

export const sendChatMessage = (query, history = [], filterDisease = null, context = {}) =>
  request('/chat', { method: 'POST', body: JSON.stringify({ query, history, filter_disease: filterDisease, ...context }) });

export const getDiseases = (params) => request(`/diseases${queryString(params)}`);
export const getDiseaseDetail = (slug) => request(`/diseases/${slug}`);

export const getHistory = () => request('/history');
export const deleteHistory = (id) => request(`/history/${id}`, { method: 'DELETE' });
export const getChatHistory = () => request('/history/chats');
export const saveChatHistory = (data) => request('/history/chats', { method: 'POST', body: JSON.stringify(data) });
export const deleteChatHistory = (id) => request(`/history/chats/${id}`, { method: 'DELETE' });

export const getTrends = () => request('/analytics/trends');
export const getTopDiseases = () => request('/analytics/top-diseases');
export const getHeatmap = () => request('/analytics/heatmap');
export const getAnalyticsSummary = () => request('/analytics/summary');
export const getOutbreakAlerts = () => request('/analytics/outbreak-alerts');
export const getAgeDistribution = () => request('/analytics/age-distribution');

export const updateNotificationPrefs = (data) =>
  request('/auth/me/notifications', { method: 'PATCH', body: JSON.stringify(data) });

export const submitChatFeedback = (data) =>
  request('/history/chats/feedback', { method: 'POST', body: JSON.stringify(data) });
export const getChatInsights = () => request('/analytics/chat-insights');

export const sendContact = (data) => request('/contact', { method: 'POST', body: JSON.stringify(data) });
export const subscribeNewsletter = (data) =>
  request('/newsletter/subscribe', { method: 'POST', body: JSON.stringify(data) });

// File upload — does NOT set Content-Type so browser sets multipart boundary automatically
async function uploadFile(path, formData) {
  const token = localStorage.getItem('mediguard_token');
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) throw new ApiError(data?.detail || 'Upload failed', res.status);
  return { data };
}

export const analyzeImage = (file, context = '') => {
  const fd = new FormData();
  fd.append('file', file);
  fd.append('context', context);
  return uploadFile('/chat/analyze-image', fd);
};
