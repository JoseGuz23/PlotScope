// =============================================================================
// api.js - SERVICIO DE CONEXIÓN CON AZURE BACKEND
// =============================================================================
// Centraliza todas las llamadas al backend de Sylphrena
// =============================================================================

// URL base del backend Azure - CAMBIAR EN PRODUCCIÓN
const API_BASE = import.meta.env.VITE_API_URL || 'https://tu-function-app.azurewebsites.net/api';

// Storage de Azure para los outputs
const STORAGE_BASE = 'https://sylphrenastorage.blob.core.windows.net/sylphrena-outputs';

// =============================================================================
// HELPER PARA FETCH
// =============================================================================

async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      // TODO: Agregar JWT cuando implementemos auth real
      // 'Authorization': `Bearer ${getToken()}`,
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || `Error ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

// =============================================================================
// PROYECTOS / JOBS
// =============================================================================

export const projectsAPI = {
  // Obtener todos los proyectos del usuario
  async getAll() {
    // TODO: Endpoint real cuando exista
    // return fetchAPI('/projects');
    
    // MOCK DATA - Reemplazar con llamada real
    return [
      {
        id: 'bb841d8a189243faa35647773561aa6f',
        name: 'Piel_Morena',
        status: 'completed',
        createdAt: '2025-12-03T17:39:01',
        wordCount: 4931,
        chaptersCount: 2,
        changesCount: 23,
      },
      {
        id: 'demo_project_002',
        name: 'La_Sombra_del_Viento',
        status: 'processing',
        createdAt: '2025-12-07T10:00:00',
        wordCount: 85240,
        chaptersCount: 25,
        progress: 45,
      },
      {
        id: 'demo_project_003',
        name: 'Cien_Años_de_Soledad',
        status: 'pending_bible',
        createdAt: '2025-12-06T08:30:00',
        wordCount: 120000,
        chaptersCount: 40,
      },
    ];
  },

  // Obtener un proyecto específico
  async getById(projectId) {
    // TODO: return fetchAPI(`/projects/${projectId}`);
    const projects = await this.getAll();
    return projects.find(p => p.id === projectId);
  },

  // Iniciar nuevo procesamiento
  async startJob(manuscriptUrl, options = {}) {
    return fetchAPI('/start-job', {
      method: 'POST',
      body: JSON.stringify({
        manuscript_url: manuscriptUrl,
        ...options,
      }),
    });
  },

  // Obtener estado del job
  async getJobStatus(jobId) {
    return fetchAPI(`/job-status/${jobId}`);
  },

  // Obtener outputs del job
  async getOutputs(jobId) {
    return fetchAPI(`/outputs/${jobId}`);
  },
};

// =============================================================================
// BIBLIA NARRATIVA
// =============================================================================

export const bibleAPI = {
  // Obtener biblia de un proyecto
  async get(projectId) {
    // Construir URL del blob storage
    const url = `${STORAGE_BASE}/${projectId}/biblia_validada.json`;
    
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error('Biblia no encontrada');
      return await response.json();
    } catch (error) {
      console.error('Error cargando biblia:', error);
      throw error;
    }
  },

  // Guardar biblia editada por el usuario
  async save(projectId, bibleData) {
    // TODO: Endpoint para guardar biblia editada
    return fetchAPI(`/projects/${projectId}/bible`, {
      method: 'PUT',
      body: JSON.stringify(bibleData),
    });
  },

  // Aprobar biblia y continuar procesamiento
  async approve(projectId) {
    // TODO: Endpoint para aprobar y continuar
    return fetchAPI(`/projects/${projectId}/bible/approve`, {
      method: 'POST',
    });
  },
};

// =============================================================================
// MANUSCRITOS Y CAMBIOS
// =============================================================================

export const manuscriptAPI = {
  // Obtener manuscrito editado
  async getEdited(projectId) {
    const url = `${STORAGE_BASE}/${projectId}/manuscrito_editado.md`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Manuscrito no encontrado');
    return await response.text();
  },

  // Obtener manuscrito anotado (con cambios inline)
  async getAnnotated(projectId) {
    const url = `${STORAGE_BASE}/${projectId}/manuscrito_anotado.md`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Manuscrito anotado no encontrado');
    return await response.text();
  },

  // Obtener control de cambios HTML
  async getChangesHTML(projectId) {
    const url = `${STORAGE_BASE}/${projectId}/control_cambios.html`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Control de cambios no encontrado');
    return await response.text();
  },

  // Obtener resumen ejecutivo
  async getSummary(projectId) {
    const url = `${STORAGE_BASE}/${projectId}/resumen_ejecutivo.json`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Resumen no encontrado');
    return await response.json();
  },
};

// =============================================================================
// UPLOAD DE ARCHIVOS
// =============================================================================

export const uploadAPI = {
  // Subir manuscrito a Azure Blob Storage
  async uploadManuscript(file, projectName) {
    // TODO: Implementar cuando tengamos endpoint de upload
    // Probablemente necesitaremos un SAS token del backend
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', projectName);
    
    return fetchAPI('/upload', {
      method: 'POST',
      headers: {}, // Sin Content-Type para FormData
      body: formData,
    });
  },
};

// =============================================================================
// EXPORT DEFAULT
// =============================================================================

export default {
  projects: projectsAPI,
  bible: bibleAPI,
  manuscript: manuscriptAPI,
  upload: uploadAPI,
};
