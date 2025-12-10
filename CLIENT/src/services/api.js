// =============================================================================
// api.js - CLIENTE API SYLPHRENA (COMPLETO 5.0)
// =============================================================================

const API_BASE = import.meta.env.VITE_API_URL || 'https://sylphrena-orchestrator-ece2a4epbdbrfbgk.westus3-01.azurewebsites.net/api';
const FUNCTION_KEY = import.meta.env.VITE_FUNCTION_KEY || '';

console.log('🔗 API CONECTADA A:', API_BASE);

function getAuthHeaders() {
  const token = localStorage.getItem('sylphrena_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE}/${endpoint}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
        ...options.headers,
      },
    });
    
    if (response.status === 401 && !endpoint.includes('auth/login')) {
      localStorage.removeItem('sylphrena_token');
      window.location.href = '/login';
      throw new Error('Sesión expirada');
    }
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Error: ${response.status}`);
    }
    
    if (response.status === 204) return null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('text/plain')) return await response.text();
    return await response.json();
  } catch (error) {
    console.error(`❌ Error en ${endpoint}:`, error);
    throw error;
  }
}

export const authAPI = {
  async login(password) {
    const response = await apiFetch('auth/login', { method: 'POST', body: JSON.stringify({ password }) });
    if (response.token) localStorage.setItem('sylphrena_token', response.token);
    return response;
  },
  logout() { localStorage.removeItem('sylphrena_token'); window.location.href = '/login'; },
  isAuthenticated() { return !!localStorage.getItem('sylphrena_token'); },
  getToken() { return localStorage.getItem('sylphrena_token'); }
};

export const projectsAPI = {
  async getAll() { const data = await apiFetch('projects'); return data.projects || []; },
  async getById(id) { return await apiFetch(`project/${id}`); },
  async getStatus(id) { return await apiFetch(`project/${id}/status`); },
  async terminate(id, reason = 'User cancelled') { return await apiFetch(`project/${id}/terminate`, { method: 'POST', body: JSON.stringify({ reason }) }); },
  async delete(id) { return await apiFetch(`project/${id}`, { method: 'DELETE' }); },
};

export const bibleAPI = {
  async get(id) { return await apiFetch(`project/${id}/bible`); },
  async save(id, data) { return await apiFetch(`project/${id}/bible`, { method: 'POST', body: JSON.stringify(data) }); },
  async approve(id) { return await apiFetch(`project/${id}/bible/approve`, { method: 'POST' }); },
};

// --- ESTO ES LO QUE TE FALTA Y CAUSA EL ERROR ---
export const editorialAPI = {
  async getLetter(projectId) { return await apiFetch(`project/${projectId}/editorial-letter`); },
  async getMarginNotes(projectId) { return await apiFetch(`project/${projectId}/margin-notes`); }
};

export const manuscriptAPI = {
  async getEdited(id) { return await apiFetch(`project/${id}/manuscript/edited`); },
  async getAnnotated(id) { return await apiFetch(`project/${id}/manuscript/annotated`); },
  async getChangesHTML(id) { return await apiFetch(`project/${id}/manuscript/changes-html`); },
  async getSummary(id) { return await apiFetch(`project/${id}`); },
  async getChanges(id) { return await apiFetch(`project/${id}/changes`); },
  async getChapters(id) { return await apiFetch(`project/${id}/chapters`); },
  async saveChangeDecision(pid, cid, action) { return await apiFetch(`project/${pid}/changes/${cid}/decision`, { method: 'POST', body: JSON.stringify({ action }) }); },
  async saveAllDecisions(pid, decisions) { return await apiFetch(`project/${pid}/changes/decisions`, { method: 'POST', body: JSON.stringify({ decisions }) }); },
  async export(id, accepted) { return await apiFetch(`project/${id}/export`, { method: 'POST', body: JSON.stringify({ accepted_changes: accepted }) }); },
};

export const uploadAPI = {
  async uploadManuscript(file, projectName) {
    const base64 = await fileToBase64(file);
    return await apiFetch('project/upload', { method: 'POST', body: JSON.stringify({ filename: file.name, projectName, content: base64 }) });
  },
  async startOrchestrator(jobId, blobPath) {
    const baseUrl = API_BASE.replace('/api', '');
    let url = `${baseUrl}/api/HttpStart${FUNCTION_KEY ? `?code=${FUNCTION_KEY}` : ''}`;
    try {
      const response = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json', ...getAuthHeaders() }, body: JSON.stringify({ job_id: jobId, blob_path: blobPath }) });
      if (!response.ok) throw new Error(`Error iniciando: ${response.status}`);
      return await response.json();
    } catch (error) { return { status: 'pending', message: 'Orquestador en cola' }; }
  },
  async analyzeForQuote(file) {
    const base64 = await fileToBase64(file);
    return await apiFetch('analyze-file', { method: 'POST', body: JSON.stringify({ filename: file.name, content: base64 }) });
  },
};

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result.split(',')[1]);
    reader.onerror = reject;
  });
}

// IMPORTANTE: Asegúrate de exportar editorialAPI aquí
export default {
  auth: authAPI,
  projects: projectsAPI,
  bible: bibleAPI,
  editorial: editorialAPI, // <--- ESTO FALTABA
  manuscript: manuscriptAPI,
  upload: uploadAPI,
};