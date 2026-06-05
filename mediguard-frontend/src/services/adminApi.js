const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const TOKEN_KEY = 'mg_admin_token';

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

async function adminRequest(path, options = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

// Auth
export const adminLogin = (email, password) =>
  adminRequest('/admin/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });

export const adminMe = () => adminRequest('/admin/auth/me');

// Stats
export const getAdminStats = () => adminRequest('/admin/stats');

// Users
export const getAdminUsers = (page = 1, limit = 20, search = '') =>
  adminRequest(`/admin/users?page=${page}&limit=${limit}&search=${encodeURIComponent(search)}`);

export const updateAdminUser = (userId, payload) =>
  adminRequest(`/admin/users/${userId}`, { method: 'PATCH', body: JSON.stringify(payload) });

export const deleteAdminUser = (userId) =>
  adminRequest(`/admin/users/${userId}`, { method: 'DELETE' });

// Newsletter
export const getAdminSubscribers = (page = 1, limit = 30, activeOnly = false) =>
  adminRequest(`/admin/newsletter?page=${page}&limit=${limit}&active_only=${activeOnly}`);

export const updateAdminSubscriber = (id, payload) =>
  adminRequest(`/admin/newsletter/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });

export const deleteAdminSubscriber = (id) =>
  adminRequest(`/admin/newsletter/${id}`, { method: 'DELETE' });

export const sendAdminNewsletter = (subject, body) =>
  adminRequest('/admin/newsletter/send', { method: 'POST', body: JSON.stringify({ subject, body }) });

export const sendAdminOutbreakAlerts = () =>
  adminRequest('/analytics/send-outbreak-alerts', { method: 'POST' });

export const sendAdminMonthlyDigest = () =>
  adminRequest('/analytics/send-monthly-digest', { method: 'POST' });

// Trends
export const getAdminTrends = (days = 30) =>
  adminRequest(`/admin/trends?days=${days}`);

// Diseases
export const getAdminDiseases = (page = 1, limit = 20, search = '') =>
  adminRequest(`/admin/diseases?page=${page}&limit=${limit}&search=${encodeURIComponent(search)}`);

export const updateAdminDisease = (slug, payload) =>
  adminRequest(`/admin/diseases/${slug}`, { method: 'PATCH', body: JSON.stringify(payload) });

// Messages
export const getAdminMessages = (page = 1, limit = 20, unreadOnly = false) =>
  adminRequest(`/admin/messages?page=${page}&limit=${limit}&unread_only=${unreadOnly}`);

export const markMessageRead = (id) =>
  adminRequest(`/admin/messages/${id}/read`, { method: 'PATCH' });

export const deleteAdminMessage = (id) =>
  adminRequest(`/admin/messages/${id}`, { method: 'DELETE' });

// Feedback
export const getAdminFeedback = (page = 1, helpful = null) =>
  adminRequest(`/admin/feedback?page=${page}${helpful !== null ? `&helpful=${helpful}` : ''}`);

export { TOKEN_KEY };
