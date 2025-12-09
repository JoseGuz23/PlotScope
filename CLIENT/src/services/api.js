// =============================================================================
// api.js - CONEXIÓN CON AZURE (API DURABLE + BLOB STORAGE)
// =============================================================================

// URLs de Azure
const API_BASE = import.meta.env.VITE_API_URL || 'https://sylphrena-orchestrator-ece2a4epbdbrfbgk.westus3-01.azurewebsites.net/api';
const STORAGE_BASE = import.meta.env.VITE_STORAGE_URL || 'https://sylphrenastorage.blob.core.windows.net/sylphrena-outputs';

console.log('🔗 API URL:', API_BASE);
console.log('🔗 Storage URL:', STORAGE_BASE);

// =============================================================================
// HELPER - Fetch con manejo de errores
// =============================================================================

async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE}/${endpoint}`;
  console.log(`📡 ${options.method || 'GET'} ${url}`);
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Error ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`❌ Error en ${endpoint}:`, error);
    throw error;
  }
}

// =============================================================================
// PROYECTOS
// =============================================================================

export const projectsAPI = {
  // Lista todos los proyectos desde la API
  async getAll() {
    try {
      const data = await apiFetch('projects');
      return data.projects || [];
    } catch (error) {
      console.warn('⚠️ API no disponible, usando datos locales');
      // Fallback a datos locales si la API falla
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
      ];
    }
  },

  // Obtiene info de un proyecto específico
  async getById(projectId) {
    try {
      return await apiFetch(`project/${projectId}`);
    } catch (error) {
      // Fallback: buscar en lista local
      const projects = await this.getAll();
      return projects.find(p => p.id === projectId);
    }
  },
};

// =============================================================================
// BIBLIA NARRATIVA
// =============================================================================

export const bibleAPI = {
  // Obtener biblia - primero intenta API, luego Blob directo
  async get(projectId) {
    // Opción 1: Desde la API
    try {
      console.log('📚 Intentando cargar biblia desde API...');
      const data = await apiFetch(`project/${projectId}/bible`);
      console.log('✅ Biblia cargada desde API');
      return data;
    } catch (apiError) {
      console.warn('⚠️ API no disponible, intentando Blob Storage directo...');
    }
    
    // Opción 2: Directo del Blob Storage
    const url = `${STORAGE_BASE}/${projectId}/biblia_validada.json`;
    console.log('📚 Cargando biblia desde Blob:', url);
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `No se pudo cargar la biblia. ` +
        `Verifica CORS en Storage Account y que el archivo exista.`
      );
    }
    
    const data = await response.json();
    console.log('✅ Biblia cargada desde Blob Storage');
    return data;
  },

  // Guardar biblia editada
  async save(projectId, bibleData) {
    console.log('💾 Guardando biblia editada...');
    return await apiFetch(`project/${projectId}/bible`, {
      method: 'POST',
      body: JSON.stringify(bibleData),
    });
  },

  // Aprobar biblia y continuar procesamiento
  async approve(projectId) {
    console.log('✅ Aprobando biblia...');
    return await apiFetch(`project/${projectId}/bible/approve`, {
      method: 'POST',
    });
  },
};

// =============================================================================
// MANUSCRITOS Y CAMBIOS
// =============================================================================

export const manuscriptAPI = {
  // Manuscrito editado (limpio) - desde Blob
  async getEdited(projectId) {
    const url = `${STORAGE_BASE}/${projectId}/manuscrito_editado.md`;
    console.log('📄 Cargando manuscrito editado...');
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Manuscrito editado no encontrado');
    return await response.text();
  },

  // Manuscrito anotado (con cambios inline) - desde Blob
  async getAnnotated(projectId) {
    const url = `${STORAGE_BASE}/${projectId}/manuscrito_anotado.md`;
    console.log('📝 Cargando manuscrito anotado...');
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Manuscrito anotado no encontrado');
    return await response.text();
  },

  // Control de cambios HTML - desde Blob
  async getChangesHTML(projectId) {
    const url = `${STORAGE_BASE}/${projectId}/control_cambios.html`;
    console.log('🔄 Cargando control de cambios HTML...');
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Control de cambios no encontrado');
    return await response.text();
  },

  // Resumen ejecutivo - desde Blob
  async getSummary(projectId) {
    const url = `${STORAGE_BASE}/${projectId}/resumen_ejecutivo.json`;
    console.log('📊 Cargando resumen ejecutivo...');
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Resumen no encontrado');
    return await response.json();
  },

  // Lista estructurada de cambios - desde API
  async getChanges(projectId) {
    return await apiFetch(`project/${projectId}/changes`);
  },

  // Guardar decisión sobre un cambio
  async saveChangeDecision(projectId, changeId, action) {
    console.log(`📝 Guardando decisión: ${changeId} -> ${action}`);
    return await apiFetch(`project/${projectId}/changes/${changeId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ action }), // 'accept' o 'reject'
    });
  },

  // Exportar manuscrito final
  async export(projectId) {
    console.log('📤 Exportando manuscrito final...');
    return await apiFetch(`project/${projectId}/export`, {
      method: 'POST',
    });
  },
};

// =============================================================================
// UPLOAD - Subir nuevo manuscrito
// =============================================================================

export const uploadAPI = {
  // Subir manuscrito e iniciar procesamiento
  async uploadManuscript(file, projectName) {
    console.log('📤 Subiendo manuscrito:', projectName);
    
    // TODO: Necesitas implementar endpoint en tu API que:
    // 1. Genere SAS token para upload
    // 2. Reciba el archivo
    // 3. Inicie el Orchestrator
    
    throw new Error(
      'Upload no implementado. Necesitas crear endpoint en tu API ' +
      'que genere SAS token y llame a HttpStart para iniciar el procesamiento.'
    );
  },

  // Iniciar procesamiento de un libro (llama a HttpStart)
  async startProcessing(bookPath) {
    console.log('🚀 Iniciando procesamiento:', bookPath);
    
    // Esto llamaría a tu HttpStart
    const response = await fetch(`${API_BASE.replace('/api', '')}/api/HttpStart`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ book_path: bookPath }),
    });
    
    if (!response.ok) {
      throw new Error('Error iniciando procesamiento');
    }
    
    return await response.json();
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
