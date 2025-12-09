// =============================================================================
// api.js - CLIENTE API SYLPHRENA (COMPLETO)
// =============================================================================

// --- CONFIGURACIÓN ---
const API_BASE = import.meta.env.VITE_API_URL || 'https://sylphrena-orchestrator-ece2a4epbdbrfbgk.westus3-01.azurewebsites.net/api';

// Function key para HttpStart (si la necesitas)
const FUNCTION_KEY = import.meta.env.VITE_FUNCTION_KEY || '';

console.log('🔗 API CONECTADA A:', API_BASE);

// =============================================================================
// HELPER - Fetch con autenticación
// =============================================================================

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
      console.warn('⚠️ Sesión expirada. Redirigiendo a login...');
      localStorage.removeItem('sylphrena_token');
      window.location.href = '/login';
      throw new Error('Sesión expirada');
    }
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Error del servidor: ${response.status}`);
    }
    
    // Manejar respuestas sin contenido (como DELETE 204)
    if (response.status === 204) {
      return null;
    }
    
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('text/plain')) {
      return await response.text();
    }
    
    return await response.json();
  } catch (error) {
    console.error(`❌ Error en ${endpoint}:`, error);
    throw error;
  }
}

// =============================================================================
// AUTH
// =============================================================================

export const authAPI = {
  async login(password) {
    const response = await apiFetch('auth/login', {
      method: 'POST',
      body: JSON.stringify({ password }),
    });
    
    if (response.token) {
      localStorage.setItem('sylphrena_token', response.token);
    }
    
    return response;
  },
  
  logout() {
    localStorage.removeItem('sylphrena_token');
    window.location.href = '/login';
  },
  
  isAuthenticated() {
    return !!localStorage.getItem('sylphrena_token');
  },
  
  getToken() {
    return localStorage.getItem('sylphrena_token');
  }
};

// =============================================================================
// PROYECTOS
// =============================================================================

export const projectsAPI = {
  async getAll() {
    const data = await apiFetch('projects');
    return data.projects || [];
  },

  async getById(projectId) {
    return await apiFetch(`project/${projectId}`);
  },
  
  async getStatus(projectId) {
    return await apiFetch(`project/${projectId}/status`);
  },

  // Detener un proceso en ejecución
  async terminate(projectId, reason = 'User cancelled') {
    return await apiFetch(`project/${projectId}/terminate`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },

  // Eliminar un proyecto
  async delete(projectId) {
    return await apiFetch(`project/${projectId}`, {
      method: 'DELETE',
    });
  },
};

// =============================================================================
// BIBLIA NARRATIVA
// =============================================================================

export const bibleAPI = {
  async get(projectId) {
    return await apiFetch(`project/${projectId}/bible`);
  },

  async save(projectId, bibleData) {
    return await apiFetch(`project/${projectId}/bible`, {
      method: 'POST',
      body: JSON.stringify(bibleData),
    });
  },

  async approve(projectId) {
    return await apiFetch(`project/${projectId}/bible/approve`, {
      method: 'POST',
    });
  },
};

// =============================================================================
// MANUSCRITOS
// =============================================================================

export const manuscriptAPI = {
  async getEdited(projectId) {
    return await apiFetch(`project/${projectId}/manuscript/edited`);
  },

  async getAnnotated(projectId) {
    return await apiFetch(`project/${projectId}/manuscript/annotated`);
  },

  async getChangesHTML(projectId) {
    return await apiFetch(`project/${projectId}/manuscript/changes-html`);
  },

  async getSummary(projectId) {
    return await apiFetch(`project/${projectId}`);
  },

  async getChanges(projectId) {
    return await apiFetch(`project/${projectId}/changes`);
  },

  async getChapters(projectId) {
    return await apiFetch(`project/${projectId}/chapters`);
  },

  async saveChangeDecision(projectId, changeId, action) {
    return await apiFetch(`project/${projectId}/changes/${changeId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ action }),
    });
  },

  async saveAllDecisions(projectId, decisions) {
    return await apiFetch(`project/${projectId}/changes/decisions`, {
      method: 'POST',
      body: JSON.stringify({ decisions }),
    });
  },

  async export(projectId, acceptedChanges) {
    return await apiFetch(`project/${projectId}/export`, {
      method: 'POST',
      body: JSON.stringify({ accepted_changes: acceptedChanges }),
    });
  },
};

// =============================================================================
// UPLOAD + ORQUESTADOR
// =============================================================================

export const uploadAPI = {
  async uploadManuscript(file, projectName) {
    const base64 = await fileToBase64(file);
    return await apiFetch('project/upload', {
      method: 'POST',
      body: JSON.stringify({
        filename: file.name,
        projectName: projectName,
        content: base64,
      }),
    });
  },

  async startOrchestrator(jobId, blobPath) {
    const baseUrl = API_BASE.replace('/api', '');
    let url = `${baseUrl}/api/HttpStart`;
    if (FUNCTION_KEY) {
      url += `?code=${FUNCTION_KEY}`;
    }
    
    console.log('🚀 Iniciando orquestador:', url);
    
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          job_id: jobId,
          blob_path: blobPath,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Error iniciando orquestador: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('❌ Error en startOrchestrator:', error);
      return { status: 'pending', message: 'Orquestador en cola' };
    }
  },

  async analyzeForQuote(file) {
    const base64 = await fileToBase64(file);
    return await apiFetch('analyze-file', {
      method: 'POST',
      body: JSON.stringify({
        filename: file.name,
        content: base64,
      }),
    });
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

export default {
  auth: authAPI,
  projects: projectsAPI,
  bible: bibleAPI,
  manuscript: manuscriptAPI,
  upload: uploadAPI,
};