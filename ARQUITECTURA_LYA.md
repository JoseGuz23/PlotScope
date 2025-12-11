# LYA: Sistema de Edición Editorial Profesional Impulsado por IA

## Documento de Arquitectura y Funcionamiento

**Versión**: 5.3
**Fecha**: Diciembre 2025
**Proyecto**: LYA (anteriormente Sylphrena)

---

## 1. ¿Qué es LYA?

LYA es un **sistema de edición editorial profesional automatizado** que funciona como un *Developmental Editor* virtual. Toma manuscritos literarios en formato DOCX y produce retroalimentación editorial de calidad profesional comparable a la que proporcionaría un editor humano experimentado.

### Propósito Central

Democratizar el acceso a edición editorial de calidad para autores que no pueden costear servicios profesionales tradicionales (que típicamente oscilan entre $2,000-$10,000 USD por manuscrito).

### Productos Finales que Genera

Cuando un autor sube su manuscrito, LYA produce:

1. **Biblia Narrativa**: Documento maestro con la identidad completa de la obra (género, tono, tema, arcos de personajes, voz autoral, mapas de ritmo, problemas priorizados)

2. **Carta Editorial Profesional**: Documento de 1,500-2,500 palabras escrito en prosa natural que imita el tono de un editor real, con fortalezas, debilidades y plan de acción

3. **Notas al Margen**: Comentarios críticos párrafo por párrafo sobre claridad, show-vs-tell, ritmo, tensión y consistencia

4. **Manuscrito Editado**: Versión corregida del texto con cambios aplicados (redundancias eliminadas, show-vs-tell mejorado, ritmo variado)

5. **Manuscrito Anotado**: Versión con cambios resaltados y explicaciones de cada corrección

6. **Tracking de Cambios**: Base de datos estructurada de cada edición realizada, con justificación, impacto narrativo y capacidad de aceptar/rechazar cambios

---

## 2. Arquitectura General del Sistema

### Componentes Principales

LYA está construido sobre **dos pilares arquitectónicos**:

#### **API_DURABLE** (Backend - Azure Durable Functions)
Motor de procesamiento basado en orquestación serverless que coordina 12 fases de análisis y edición secuenciales. Utiliza Azure Durable Functions para mantener estado complejo a través de workflows de larga duración (30-50 minutos por libro).

**Tecnologías core**:
- Python 3.9+
- Azure Durable Functions (pattern: Function Chaining + Human Interaction)
- Azure Blob Storage (persistencia de manuscritos y resultados)
- Google Gemini API (análisis estructural, cualitativo y síntesis)
- Anthropic Claude API (edición de prosa y notas críticas)

#### **CLIENT** (Frontend - React Web Application)
Interfaz de usuario moderna para subir manuscritos, monitorear progreso, revisar la Biblia Narrativa y trabajar con resultados.

**Tecnologías core**:
- React 19 + React Router 7
- Vite (bundler experimental con rolldown)
- TailwindCSS 4
- TipTap (editor WYSIWYG)
- docx.js (generación de archivos Word)

### Stack Tecnológico Completo

```
┌─────────────────────────────────────────────────────────┐
│                    USUARIO (Autor)                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              FRONTEND (CLIENT - React)                  │
│  - Upload manuscritos (.docx)                           │
│  - Monitoreo de progreso en tiempo real                │
│  - Revisión y aprobación de Biblia Narrativa           │
│  - Editor de manuscritos con tracking de cambios       │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS/REST API
                       ▼
┌─────────────────────────────────────────────────────────┐
│         BACKEND (Azure Durable Functions)               │
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │      Orchestrator (12 Fases Secuenciales)     │     │
│  └───────────────────────────────────────────────┘     │
│                       │                                 │
│         ┌─────────────┼─────────────┐                  │
│         ▼             ▼             ▼                  │
│   ┌─────────┐  ┌──────────┐  ┌──────────┐            │
│   │ Gemini  │  │  Claude  │  │  Azure   │            │
│   │   API   │  │   API    │  │  Blob    │            │
│   └─────────┘  └──────────┘  └──────────┘            │
│   (Análisis)   (Edición)     (Storage)                │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Flujo Completo: Del Manuscrito al Documento Editado

### Visión de Alto Nivel

El proceso completo sigue este flujo lógico:

```
Manuscrito.docx
    → Segmentación inteligente en capítulos/fragmentos
    → Análisis multi-capa (factual → estructural → cualitativo)
    → Síntesis en Biblia Narrativa
    → [APROBACIÓN HUMANA]
    → Generación de carta editorial
    → Edición profesional guiada por Biblia
    → Reconstrucción de manuscrito editado
    → Entrega de paquete completo
```

### Las 12 Fases del Orquestador

El orquestador de Durable Functions ejecuta 12 fases secuenciales, cada una construyendo sobre los resultados anteriores:

---

#### **FASE 1: Segmentación del Manuscrito**

**Objetivo**: Dividir el manuscrito en unidades procesables (capítulos y fragmentos).

**Proceso**:
- Lee el archivo .docx desde Azure Blob Storage usando la biblioteca `python-docx`
- Detecta capítulos mediante análisis de patrones regex que buscan palabras clave como "Capítulo", "Prólogo", "Epílogo", "Interludio"
- Identifica tipos de sección especiales (prólogos, epílogos, notas del editor, actos, partes)
- Para capítulos muy largos (>12,000 caracteres), aplica división inteligente respetando límites de párrafo (busca `\n\n` → `\n` → `.`)
- Genera metadata jerárquica para cada fragmento: `fragment_id`, `parent_chapter_id`, `section_type`, `fragment_index`, `total_fragments`

**Tecnología**: python-docx para parsing, regex para detección de estructura.

**Salida**: Lista de fragmentos con contenido de texto plano y metadata estructurada.

**Razón de ser**: Los modelos de IA tienen límites de tokens (~1M tokens en Gemini, ~200k en Claude). Segmentar permite procesar libros de cualquier tamaño y paralelizar el análisis.

---

#### **FASE 2: Análisis Factual (Capa 1) - Batch API**

**Objetivo**: Extraer hechos objetivos de cada fragmento (personajes, eventos, métricas).

**Proceso**:
- Envía TODOS los fragmentos en un único batch a Google Gemini Batch API
- Utiliza el modelo `gemini-1.5-flash-002` (optimizado para velocidad y costo)
- Para cada fragmento, el modelo extrae:
  - **Personajes**: Protagonistas, antagonistas, secundarios con roles y características
  - **Secuencia de eventos**: Cronología de lo que ocurre en el fragmento
  - **Métricas básicas**: Total de palabras, párrafos, porcentaje de diálogo, ritmo estimado
  - **Señales tempranas de edición**: Problemas evidentes detectados
- Polling adaptativo: Consulta el estado del batch con intervalos crecientes (10s → 15s → 20s... hasta 45s max)
- Si algunos fragmentos fallan, aplica rescate individual usando llamadas directas

**Tecnología**: Google Gemini Batch API con polling adaptativo implementado mediante `time.sleep()` con intervalos calculados dinámicamente.

**Salida**: Lista de análisis factuales por fragmento en formato JSON estructurado.

**Optimización clave**: Batch API reduce de 20 llamadas secuenciales (20+ minutos) a 1 llamada paralela (~2-5 minutos).

---

#### **FASE 3: Consolidación de Fragmentos**

**Objetivo**: Unir análisis fragmentados en capítulos completos coherentes.

**Proceso**:
- Agrupa fragmentos por `parent_chapter_id`
- Fusiona análisis de personajes eliminando duplicados (matching por nombre y aliases)
- Reconstruye la secuencia cronológica de eventos uniendo fragmentos en orden
- Agrega métricas sumando totales (palabras, párrafos) y promediando scores
- **CRITICAL FIX v5.1**: Reinyecta el contenido de texto original desde fragmentos para que las fases posteriores tengan acceso al texto completo
- Identifica capítulos incompletos (si faltan fragmentos intermedios)

**Tecnología**: Lógica de agregación en Python puro, uso de diccionarios para indexación eficiente.

**Salida**: Lista de capítulos consolidados con análisis completo de Capa 1 + contenido de texto.

**Razón de ser**: Las fases posteriores necesitan contexto de capítulo completo, no fragmentos aislados. Esta fase convierte granularidad fina en granularidad útil.

---

#### **FASES 4+5: Análisis Paralelo (Capas 2 y 3)**

**Objetivo**: Profundizar el análisis con perspectivas estructurales y cualitativas en paralelo.

**Proceso de Paralelización**:
- Usa `context.task_all([submit_layer2, submit_layer3])` de Durable Functions para ejecutar ambas fases simultáneamente
- Ambas envían batches independientes a Gemini Pro
- Polling paralelo hasta que ambos completen

##### **CAPA 2 - Análisis Estructural**
**Motor**: Google Gemini Pro (`gemini-2.0-flash-exp` o `gemini-3-pro-preview`)

Analiza por cada capítulo:
- **Componentes narrativos**: Exposición, conflicto, clímax, resolución (estructura clásica)
- **Dinámica de escenas**: Proporción de acción/diálogo/reflexión
- **Arcos de personajes detectados**: Cambios emocionales y de objetivo
- **Hooks y payoffs**: Setups abiertos (promesas narrativas) y resoluciones cumplidas
- **Score estructural**: Evaluación de qué tan bien estructurado está el capítulo (0-10)

##### **CAPA 3 - Análisis Cualitativo**
**Motor**: Google Gemini Pro

Analiza por cada capítulo:
- **Show vs Tell**: Score + ejemplos problemáticos de "telling" que debería ser "showing"
- **Economía narrativa**: Redundancias, verbosidad, información innecesaria
- **Claridad espaciotemporal**: ¿El lector puede visualizar dónde/cuándo ocurre la acción?
- **Consistencia de voz**: ¿La voz narrativa se mantiene estable?
- **Engagement/Resonancia emocional/Memorabilidad**: Scores de impacto en el lector
- **Problemas detectados**: Lista priorizada con severidad (alta/media/baja)
- **Prioridad de edición**: Ranking de qué debe corregirse primero

**Salida**: Ambas capas se inyectan en los capítulos consolidados, enriqueciendo la estructura de datos.

**Optimización**: Ejecutar en paralelo ahorra ~5-8 minutos comparado con secuencial.

---

#### **FASE 6: Creación de la Biblia Narrativa**

**Objetivo**: Sintetizar TODO el conocimiento adquirido en un documento maestro que define la identidad de la obra.

**Motor**: Google Gemini Pro con JSON Schema estricto.

**Inputs que consume**:
- Capítulos consolidados (con Capas 1, 2 y 3)
- Análisis holístico previo (lectura rápida del manuscrito completo)
- Metadata del libro

**Estructura de la Biblia Generada**:

```json
{
  "identidad_obra": {
    "genero": "Fantasía Oscura (Grimdark)",
    "subgenero": "Horror Psicológico",
    "tono": "Visceral, opresivo, sensorial",
    "tema_central": "Fragilidad humana frente a la crueldad",
    "contrato_lector": "Inmersión en mundo brutal sin concesiones",
    "estilo_narrativo": "TERCERA_LIMITADA"
  },

  "arco_narrativo": {
    "estructura_detectada": "TRES_ACTOS",
    "gancho_inicial": "Descripción del hook",
    "inciting_incident": "Evento desencadenante",
    "giros_principales": ["Giro 1", "Giro 2"],
    "climax": "Clímax detectado",
    "resolucion": "Tipo de resolución"
  },

  "reparto_completo": [
    {
      "nombre": "Ana",
      "rol": "PROTAGONISTA",
      "arquetipo": "La Sobreviviente / La Víctima",
      "arco": "De vulnerabilidad a [spoiler evitado]",
      "consistencia_score": 8,
      "notas": "Bien desarrollada pero necesita más agencia"
    }
  ],

  "voz_autor": {
    "estilo": "POETICO",
    "longitud_oraciones": "MIXTAS",
    "recursos_distintivos": ["Metáforas sensoriales", "Repetición lírica"],
    "NO_CORREGIR": [
      "Término inventado 'Cuernomuro'",
      "Uso de 'cobertijo' (regionalismo)",
      "Descripciones explícitas de violencia (son intencionales)"
    ]
  },

  "mapa_ritmo": {
    "patron_global": "ALTERNANCIA_TENSION_ALIVIO",
    "ritmo_por_capitulo": [
      {"chapter_id": 1, "ritmo": "LENTO", "razon": "Establecimiento de atmósfera"},
      {"chapter_id": 2, "ritmo": "RAPIDO", "razon": "Secuencia de acción"}
    ]
  },

  "problemas_priorizados": [
    {
      "tipo": "DISTANCIA_PSIQUICA",
      "severidad": "CRITICA",
      "descripcion": "Falta de acceso a pensamientos de Ana",
      "capitulos_afectados": [1, 2, 3],
      "sugerencia": "Intercalar monólogo interior"
    }
  ],

  "guia_para_claude": {
    "instrucciones_globales": "Mantener tono oscuro sin suavizar violencia...",
    "patrones_mantener": ["Repetición de 'frío'", "Descripciones óseas"],
    "capitulos_especiales": [
      {"chapter_id": 1, "nota": "Primer capítulo: preservar ritmo lento"}
    ]
  },

  "metricas_globales": {
    "coherencia_score": 8,
    "logica_causal_score": 8,
    "estructura_score": 8.3,
    "score_global": 8.1
  }
}
```

**Función crítica**: La Biblia es la **fuente de verdad** para todas las fases siguientes. Define:
- Qué NO debe corregirse (elementos estilísticos intencionales)
- Voz autoral a preservar
- Problemas priorizados a atacar
- Contexto narrativo para entender decisiones editoriales

**Salida**: Archivo JSON que se guarda en Blob Storage y se pasa a todas las fases posteriores.

---

#### **PAUSA PARA APROBACIÓN HUMANA**

**Punto de control crítico**: El orquestador entra en modo de espera (`WaitForExternalEvent("BibleApproved")`).

**Flujo de aprobación**:
1. Usuario revisa la Biblia en la interfaz web (`BibleReview.jsx`)
2. Puede editar secciones si la IA malinterpretó algo
3. Guarda cambios con `POST /project/{id}/bible`
4. Cuando aprueba: `POST /project/{id}/bible/approve` envía evento "BibleApproved"
5. El orquestador se reanuda y continúa con Fase 7

**Razón de ser**: La Biblia define decisiones editoriales fundamentales. Si la IA malinterpreta el género o el tono, todas las fases posteriores serán incorrectas. La aprobación humana garantiza que el análisis es preciso antes de invertir en edición costosa.

**Tiempo de pausa**: Variable (minutos a horas o días, según disponibilidad del autor).

---

#### **FASE 7: Generación de Carta Editorial**

**Objetivo**: Producir un documento en prosa natural que imite la carta que enviaría un editor profesional.

**Motor**: Google Gemini Pro en modo texto plano (no JSON).

**Inputs**:
- Biblia Narrativa completa
- Capítulos consolidados (resumen)
- Fragmentos originales (contexto de problemas específicos)

**Estructura del Prompt**:
El prompt solicita explícitamente una carta de 1,500-2,500 palabras con estructura clásica de editorial letter:
- Saludo personal y primeras impresiones
- Fortalezas principales (3-5 párrafos con ejemplos específicos)
- Áreas de mejora (5-8 párrafos, problemas priorizados de mayor a menor severidad)
- Personajes y arcos (2-4 párrafos de análisis)
- Estructura y ritmo (1-3 párrafos)
- Notas breves por capítulo
- Próximos pasos (top 3-5 prioridades) y cierre alentador

**Restricciones explícitas**:
- SIN emojis
- SIN secciones numeradas tipo reporte
- SIN subtítulos (H2, H3)
- Prosa continua en markdown
- Tono profesional pero cálido (no robótico)

**Salida**: Archivo markdown + metadata (longitud en caracteres/palabras).

**Ejemplo real (fragmento de Ana.docx)**:
> "Estimada Ana,
> Ha sido un verdadero privilegio sumergirme en el borrador de tu novela. Desde las primeras líneas, queda claro que no tienes miedo de llevar al lector a lugares oscuros, incómodos y profundamente humanos. Tu manuscrito posee una cualidad visceral que es rara de encontrar..."

**Tiempo estimado**: 60-90 segundos.

---

#### **FASE 8: Generación de Notas al Margen (Claude Batch API)**

**Objetivo**: Crear comentarios críticos párrafo por párrafo como haría un editor humano al margen del manuscrito.

**Motor**: Anthropic Claude 3.7 Sonnet via Batch API.

**Proceso**:
- Envía un batch con TODOS los capítulos
- Por cada capítulo, Claude recibe:
  - Contenido del capítulo
  - Carta editorial (para entender prioridades globales)
  - Biblia Narrativa (para contexto de voz y tono)
  - Metadata del libro
- Claude genera notas críticas específicas con esta estructura:

```json
{
  "nota_id": "ch2-nota-001",
  "parrafo_aprox": 1,
  "texto_referencia": "El cuerpo de Ana no podía parar de temblar...",
  "tipo": "claridad",
  "severidad": "media",
  "nota": "El lector termina el capítulo anterior y se encuentra desorientado. No hay transición temporal ni espacial clara entre capítulos.",
  "sugerencia": "Considera anclar al lector con un detalle sensorial o temporal que conecte con el final del capítulo anterior. Por ejemplo: 'Habían pasado dos horas desde...' o 'El olor a sangre aún...'",
  "impacto_si_no_se_corrige": "El lector comienza el capítulo confundido sobre la línea temporal, rompiendo inmersión."
}
```

**Tipos de notas**:
- `claridad`: Confusión sobre espacio/tiempo/eventos
- `show_tell`: Casos de "telling" que deberían ser "showing"
- `ritmo`: Problemas de pacing (demasiado lento/rápido)
- `tension`: Falta de stakes o pérdida de engagement
- `personaje`: Inconsistencias o falta de desarrollo
- `voz`: Desviaciones del tono establecido

**Polling adaptativo**: Intervalos de 20s → 35s → 50s... hasta 90s max.

**Salida**: Diccionario de listas de notas organizadas por `chapter_id`.

**Tiempo estimado**: 10-15 minutos para libro de 20 capítulos.

**Razón de usar Claude**: Superior en crítica constructiva y explicaciones pedagógicas (vs Gemini que es mejor en análisis estructurado).

---

#### **FASE 9: Mapas de Arcos (Gemini Pro Batch)**

**Objetivo**: Crear guías de continuidad para que la edición no rompa elementos narrativos críticos.

**Motor**: Google Gemini Pro Batch API.

**Análisis por capítulo**:
- **Elementos de worldbuilding introducidos**: Qué información nueva sobre el mundo se revela
- **Setups y payoffs**: Configuraciones abiertas (promesas) vs resoluciones logradas
- **Estado emocional de protagonistas**: Al inicio y final del capítulo (tracking de arco emocional)
- **Posición en estructura de 3 actos**: ¿En qué parte de la estructura está este capítulo?
- **Elementos críticos para continuidad**: Objetos, información, relaciones que NO pueden alterarse sin romper lógica
- **Notas para el editor**: Qué preservar absolutamente, qué puede revisarse

**Salida**: Diccionario de arc_maps por `chapter_id`.

**Razón de ser**: Previene que la edición automática rompa la lógica causal. Ejemplo: Si en capítulo 3 el personaje pierde una espada y en capítulo 5 la usa, el editor no puede eliminar la mención de pérdida.

---

#### **FASE 10: Edición Profesional (Claude Batch API)**

**Objetivo**: Aplicar correcciones de prosa manteniendo la voz autoral y respetando la Biblia.

**Motor**: Anthropic Claude 3.7 Sonnet via Batch API.

**Inputs completos por capítulo** (contexto masivo):
- Contenido del capítulo completo
- Biblia Narrativa (identidad, voz, NO_CORREGIR)
- Capítulos consolidados (contexto global del manuscrito)
- Mapa de arcos del capítulo (continuidad)
- Notas de margen (prioridades específicas)
- Metadata del libro

**Prompt de Edición Profesional** (estructura lógica):

```
IDENTIDAD DE LA OBRA:
Género: [...]
Tono: [...]
Tema: [...]
Estilo Narrativo: [...]

RESTRICCIONES ABSOLUTAS (NO_CORREGIR):
- [Lista de elementos que NO deben cambiarse]
- Mantener voz del autor: [descripción de voz]

INFORMACIÓN DEL CAPÍTULO:
Posición: Capítulo X de Y
Ritmo detectado: [RÁPIDO/MEDIO/LENTO]
Personajes presentes: [...]

NOTAS DE MARGEN (priorizar estas correcciones):
[Lista de notas con párrafo_aprox, tipo, severidad]

PROBLEMAS DETECTADOS EN ANÁLISIS:
[Problemas de Capa 3 con severidad]

TEXTO A EDITAR:
[Contenido del capítulo]

---

CRITERIOS DE EDICIÓN PROFESIONAL:

PROSA:
- Eliminar redundancias ("subir hacia arriba" → "subir")
- Sustituir verbos débiles + adverbio por verbos fuertes
- Reducir muletillas innecesarias
- Eliminar clichés
- Variar longitud de oraciones para ritmo

NARRATIVA:
- Convertir "telling" en "showing" cuando sea apropiado
- Añadir profundidad emocional interna
- Clarificar imágenes ambiguas
- Mejorar transiciones entre escenas
- Añadir anclaje sensorial donde falte

DIÁLOGO:
- Garantizar naturalidad (habla real vs escrita)
- Diferenciar voces de personajes
- Eliminar exposición forzada en diálogos
- Reducir tags de diálogo redundantes
- Incorporar subtexto

CONSISTENCIA:
- Mantener voz narrativa estable
- Verificar tiempo verbal consistente
- Respetar POV establecido
- Preservar detalles establecidos en capítulos anteriores

---

FORMATO DE RESPUESTA (JSON):
{
  "capitulo_editado": "texto corregido completo",
  "cambios_aplicados": [
    {
      "tipo": "redundancia",
      "original": "texto original",
      "editado": "texto corregido",
      "justificacion": "explicación del cambio",
      "impacto_narrativo": "bajo/medio/alto"
    }
  ]
}
```

**Proceso de Claude**:
- Lee el capítulo completo con todo el contexto
- Identifica problemas según criterios
- Aplica correcciones quirúrgicas (no reescribe todo, solo corrige lo problemático)
- Documenta CADA cambio con justificación

**Salida**: Lista de fragmentos editados con:
- `contenido_editado`: Texto corregido
- `cambios_estructurados`: Lista de modificaciones con tipo, original/editado, justificación, impacto

**Tiempo estimado**: 15-20 minutos para libro de 20 capítulos.

**Optimización**: Batch API procesa todos los capítulos en paralelo en backend de Anthropic.

---

#### **FASE 11: Reconstrucción del Manuscrito**

**Objetivo**: Ensamblar fragmentos editados en manuscritos completos y generar tracking de cambios.

**Proceso**:

1. **Sanitización de contenido**:
   - Elimina preámbulos de IA ("Aquí está el texto editado...")
   - Limpia markdown residual (```json, ``` wrappers)
   - Elimina código o metadatos que Claude pueda haber incluido

2. **Stitching inteligente**:
   - Une fragmentos editados en orden secuencial
   - Inserta doble salto de línea entre fragmentos para separación visual
   - Valida que no haya contenido vacío

3. **Generación de versiones**:
   - **Manuscrito Original**: Texto sin editar (para comparación)
   - **Manuscrito Editado**: Solo texto editado limpio
   - **Manuscrito Anotado**: Texto editado + resaltados de cambios + notas explicativas en formato markdown

4. **Extracción de cambios estructurados**:
   Procesa los `cambios_aplicados` de cada fragmento y genera:

```json
{
  "change_id": "ch1-change-000",
  "chapter_id": 1,
  "tipo": "redundancia",
  "original": "Ana no alcanzó a reaccionar a tiempo.",
  "editado": "Ana no alcanzó a reaccionar.",
  "justificacion": "'A tiempo' es redundante con 'no alcanzó a reaccionar', ya que implica que el tiempo fue insuficiente.",
  "impacto_narrativo": "bajo",
  "status": "accepted",
  "position": {
    "paragraph_index": 0,
    "word_start": 14,
    "word_end": 21,
    "context_before": "madera contra el hueso retumbó por toda la choza.",
    "context_after": "El hijo de la familia era demasiado rápido..."
  }
}
```

5. **Generación de estadísticas**:
   - Total de cambios aplicados
   - Cambios por tipo (redundancia, show_tell, etc.)
   - Cambios por capítulo
   - Distribución de impacto narrativo

**Salida**:
- `manuscripts`: {original, edited, annotated} en texto markdown
- `consolidated_chapters`: Capítulos con contenido editado inyectado
- `cambios_estructurados`: Lista completa de cambios
- `statistics`: Métricas agregadas

**Razón de ser**: Convierte ediciones fragmentadas en productos finales coherentes y proporciona tracking granular para aceptar/rechazar cambios.

---

#### **FASE 12: Guardado de Resultados en Azure Blob Storage**

**Objetivo**: Persistir todos los artefactos generados en almacenamiento permanente.

**Proceso**:
Sube a Azure Blob Storage (container: `sylphrena-outputs/{job_id}/`):

1. **metadata.json**: Info del proyecto
   - `job_id`, `book_name`, `version`, `created_at`, `status`
   - Counts (total de capítulos, fragmentos, cambios)

2. **biblia_validada.json**: Biblia Narrativa completa

3. **biblia_narrativa.md**: Versión en markdown legible de la Biblia

4. **carta_editorial.json**: Carta + metadata (longitud)

5. **carta_editorial.md**: Carta en markdown

6. **notas_margen.json**: Notas de margen organizadas por capítulo

7. **capitulos_consolidados.json**: Capítulos con todos los análisis (Capas 1/2/3, arcos, contenido editado)

8. **cambios_estructurados.json**: Lista de cambios con decision tracking

9. **reporte_cambios.md**: Reporte legible de cambios en markdown

10. **resumen_ejecutivo.json**: Índice de todos los archivos con URLs de Blob Storage + estadísticas

**Formato de URLs**:
```
https://sylphrenastorage.blob.core.windows.net/sylphrena-outputs/{job_id}/biblia_validada.json
```

**Respuesta final al cliente**:
```json
{
  "status": "completed",
  "job_id": "Ana_20251211_045613",
  "manuscripts": {
    "original": "texto original completo...",
    "edited": "texto editado completo...",
    "annotated": "texto anotado completo..."
  },
  "statistics": {
    "total_changes": 42,
    "changes_by_type": {...}
  },
  "bible_url": "https://...",
  "carta_url": "https://...",
  "processing_time_seconds": 1847
}
```

**Tiempo estimado**: 10-15 segundos.

---

## 4. Tecnologías y Metodologías Clave

### 4.1. Azure Durable Functions

**Patrón arquitectónico**: Function Chaining + Human Interaction Pattern

**Razón de uso**:
- Workflows de larga duración (30-50 minutos) sin mantener servidor activo
- Persistencia automática de estado entre fases
- Capacidad de esperar eventos externos (aprobación de Biblia)
- Reintentos automáticos y manejo de errores

**Cómo funciona**:
```python
@app.orchestration_trigger(context_name="context")
def orchestrator_function(context):
    # Fase 1
    fragments = yield context.call_activity("SegmentBook", input1)

    # Fase 2
    layer1 = yield context.call_activity("SubmitBatchAnalysis", fragments)
    layer1 = yield context.call_activity("PollBatchResult", layer1)

    # ...

    # Espera aprobación humana
    bible_approved = yield context.wait_for_external_event("BibleApproved")

    # Continúa con fases posteriores
    # ...
```

El orquestador se pausa entre `yield` statements. El runtime de Azure guarda el estado y lo reanuda cuando la actividad termina.

### 4.2. Batch APIs (Gemini y Claude)

**Problema que resuelven**:
Procesar 20 capítulos con llamadas individuales = 20 requests secuenciales = 20+ minutos.

**Solución**:
Batch APIs permiten enviar N solicitudes en 1 request. El proveedor (Google/Anthropic) las procesa en paralelo en su backend.

**Flujo de Batch API**:
```
1. Submit: POST /v1/batches con lista de requests → Devuelve batch_id
2. Poll: GET /v1/batches/{batch_id} cada X segundos
3. Status: "processing" → "processing" → ... → "completed"
4. Fetch: GET /v1/batches/{batch_id}/results → Lista de respuestas
```

**Implementación de polling adaptativo**:
```python
def get_adaptive_interval(batch_type, attempt):
    if batch_type == "gemini_flash":
        intervals = [10, 15, 20, 25, 30, 35, 40, 45]  # segundos
    elif batch_type == "claude":
        intervals = [20, 35, 50, 65, 80, 90]

    return intervals[min(attempt, len(intervals)-1)]
```

**Beneficio**: Reduce tiempo de 60-90 minutos a 30-50 minutos.

### 4.3. División de Trabajo entre Gemini y Claude

**Google Gemini**:
- Análisis estructurado (JSON schemas)
- Síntesis de información (Biblia)
- Análisis cuantitativo (scores, métricas)
- Mayor ventana de contexto (1M tokens)
- Más económico para análisis masivo

**Anthropic Claude**:
- Edición de prosa (mejor comprensión de voz autoral)
- Crítica constructiva (notas de margen)
- Tareas de escritura creativa
- Superior en seguir restricciones complejas (NO_CORREGIR)

**Razón estratégica**: Usar la herramienta óptima para cada tarea reduce costos y mejora calidad.

### 4.4. Segmentación Inteligente

**Desafío**: Modelos tienen límites de tokens. Un libro de 80k palabras puede ser ~120k tokens, pero un capítulo de 8k palabras = ~12k tokens (procesable).

**Estrategia de segmentación**:
1. Detectar capítulos con regex
2. Si capítulo < 12k chars: procesar completo
3. Si capítulo > 12k chars: dividir en fragmentos de ~10k chars respetando párrafos
4. Asignar metadata jerárquica (fragment_id, parent_chapter_id)
5. Procesar fragmentos independientemente
6. Consolidar resultados en capítulos completos

**Ventaja**: Permite procesar libros de cualquier tamaño sin exceder límites de tokens.

### 4.5. Biblia Narrativa como Fuente de Verdad

**Concepto central**: La Biblia es un documento maestro generado en Fase 6 que define la identidad completa de la obra y sirve como referencia para todas las decisiones editoriales posteriores.

**Componentes críticos**:
- **identidad_obra**: Género, tono, tema (define qué tipo de edición aplicar)
- **voz_autor**: Estilo, recursos distintivos, NO_CORREGIR (previene sobrecorrección)
- **arco_narrativo**: Estructura detectada (informa decisiones de ritmo)
- **problemas_priorizados**: Qué atacar primero (guía enfoque de edición)
- **guia_para_claude**: Instrucciones específicas para el editor de IA

**Flujo de datos**:
```
Biblia → Carta Editorial (usa problemas_priorizados)
Biblia → Notas de Margen (usa voz_autor, tono)
Biblia → Edición Profesional (usa NO_CORREGIR, voz_autor, guía)
```

**Razón de aprobación humana**: Si la Biblia malinterpreta el género (detecta "romance" cuando es "thriller"), toda la edición será incorrecta. La aprobación garantiza precisión.

---

## 5. Optimizaciones de Performance (Versión 5.1+)

### 5.1. Polling Adaptativo

**Problema**: Polling fijo tiene trade-off:
- Intervalo corto (5s): Muchas llamadas API → costo innecesario
- Intervalo largo (60s): Espera excesiva → UX pobre

**Solución**: Incrementar intervalo gradualmente.

```python
# Gemini Flash: Rápido, empieza con 10s
attempt = 0
while status != "completed":
    interval = get_adaptive_interval("gemini_flash", attempt)
    time.sleep(interval)  # 10s → 15s → 20s → ... → 45s
    status = check_batch_status(batch_id)
    attempt += 1
```

**Resultado**: Equilibrio óptimo entre latencia y costo de polling.

### 5.2. Paralelización de Capas 4+5

**Antes (v5.0)**:
```
Capa 2 (Estructural): Submit → Poll → Complete (5 min)
Capa 3 (Cualitativo): Submit → Poll → Complete (5 min)
TOTAL: 10 minutos
```

**Después (v5.1)**:
```python
task_layer2 = context.call_activity("SubmitGeminiProBatch", layer2_input)
task_layer3 = context.call_activity("SubmitGeminiProBatch", layer3_input)

[batch2_id, batch3_id] = yield context.task_all([task_layer2, task_layer3])

# Polling paralelo
while not (status2 == "completed" and status3 == "completed"):
    # Poll ambos
    # ...

TOTAL: ~6 minutos (ahorro de 40%)
```

**Razón**: Ambas capas son independientes y pueden ejecutarse simultáneamente.

### 5.3. Content Injection Fix (v5.1)

**Problema en v5.0**:
- Fase 2 analiza fragmentos (tiene texto)
- Fase 3 consolida análisis (NO tenía texto)
- Fase 10 edita capítulos → ¡No hay texto para editar!

**Solución**:
```python
# En ConsolidateFragmentAnalyses
for chapter in consolidated_chapters:
    chapter_id = chapter["chapter_id"]
    fragments = [f for f in original_fragments if f["metadata"]["parent_chapter_id"] == chapter_id]

    # Reinyectar contenido
    chapter["content"] = "\n\n".join([f["content"] for f in fragments])
```

**Resultado**: Fase 10 ahora tiene acceso al texto completo para editar.

### 5.4. Batch APIs vs Llamadas Secuenciales

**Benchmark (libro de 20 capítulos)**:

| Método | Tiempo | Costo |
|--------|--------|-------|
| Llamadas individuales secuenciales | ~60 min | $3.50 |
| Batch API con polling fijo (30s) | ~25 min | $3.00 |
| Batch API con polling adaptativo | ~18 min | $3.00 |

**Ahorro total**: ~70% de tiempo.

---

## 6. Interfaz de Usuario (CLIENT)

### 6.1. Flujo de Usuario Completo

**Paso 1: Autenticación**
- Usuario accede a `Landing.jsx`
- Click en "Empezar" → Redirige a `Login.jsx`
- Ingresa password único compartido
- Recibe JWT token → Almacenado en localStorage

**Paso 2: Subida de Manuscrito**
- Navega a `Upload.jsx`
- Drag & drop de archivo .docx (o click para seleccionar)
- Ingresa título de la obra
- Click en "Subir Manuscrito"
- Frontend llama:
  1. `uploadAPI.uploadManuscript()` → Sube .docx a Blob Storage
  2. `uploadAPI.startOrchestrator()` → Inicia procesamiento
- Recibe `job_id` → Redirige a `/proyecto/{job_id}/status`

**Paso 3: Monitoreo de Progreso**
- `ProjectStatus.jsx` hace polling cada 5-10s:
  ```javascript
  const pollStatus = async () => {
    const status = await projectsAPI.getStatus(jobId)
    setProcessingStatus(status)

    if (status.runtimeStatus === "Completed") {
      // Detener polling, mostrar éxito
    }
  }
  ```
- Visualiza timeline de fases completadas
- Muestra estado: "Processing", "Waiting for Bible Approval", "Completed"

**Paso 4: Revisión de Biblia**
- Cuando status = "Waiting for Bible Approval", habilita pestaña "Biblia"
- Usuario navega a `/proyecto/{job_id}/biblia`
- `BibleReview.jsx` carga biblia:
  ```javascript
  const bible = await bibleAPI.get(jobId)
  ```
- Interfaz interactiva con secciones expandibles:
  - Identidad de la Obra
  - Arco Narrativo
  - Reparto Completo
  - Voz del Autor
  - Mapa de Ritmo
  - Problemas Priorizados
  - Guía para Claude
- Usuario puede editar secciones en texto JSON
- Click en "Guardar Cambios":
  ```javascript
  await bibleAPI.save(jobId, editedBible)
  ```
- Click en "Aprobar Biblia":
  ```javascript
  await bibleAPI.approve(jobId)
  // Envía evento "BibleApproved" al orquestador
  ```
- Orquestador se reanuda → Status vuelve a "Processing"

**Paso 5: Revisión de Resultados**
- Cuando status = "Completed", habilita pestaña "Resultados"
- Usuario navega a `/proyecto/{job_id}/resultados`
- `ResultsHub.jsx` muestra subnavegación:
  - **Carta Editorial**
  - **Manuscrito Editado**

**Paso 5a: Carta Editorial**
- `EditorialLetter.jsx` carga carta:
  ```javascript
  const letter = await editorialAPI.getLetter(jobId)
  ```
- Renderiza markdown con ReactMarkdown
- Botón "Descargar en Word" genera .docx con docx.js

**Paso 5b: Editor de Manuscrito**
- `Editorfinal.jsx` carga:
  ```javascript
  const edited = await manuscriptAPI.getEdited(jobId)
  const changes = await manuscriptAPI.getChanges(jobId)
  ```
- Visualización lado-a-lado:
  - Izquierda: Manuscrito original
  - Derecha: Manuscrito editado con cambios resaltados
- TipTap editor WYSIWYG para visualización
- Lista de cambios con botones "Aceptar" / "Rechazar":
  ```javascript
  const handleAccept = async (changeId) => {
    await manuscriptAPI.saveChangeDecision(jobId, changeId, "accepted")
  }
  ```
- Botón "Exportar Manuscrito Final":
  ```javascript
  const final = await manuscriptAPI.export(jobId, decisions)
  // Descarga .docx con cambios aceptados aplicados
  ```

### 6.2. Componentes Principales

**Layout & Navigation**:
- `Layout.jsx`: Wrapper con header, sidebar, footer
- `ProjectLayout.jsx`: Layout de proyecto con tabs (Status, Biblia, Resultados)
- `PublicNavbar.jsx`: Navegación pública (Landing, Features, Pricing)

**Páginas Públicas**:
- `Landing.jsx`: Hero section, features, testimonios, CTA
- `Features.jsx`: Características detalladas del producto
- `Pricing.jsx`: Planes de precios
- `Login.jsx`: Autenticación

**Páginas Protegidas**:
- `Dashboard.jsx`: Lista de proyectos con estado y fecha
- `Upload.jsx`: Formulario de subida
- `ProjectStatus.jsx`: Monitoreo de progreso
- `BibleReview.jsx`: Editor de Biblia
- `ResultsHub.jsx`: Hub de resultados
- `EditorialLetter.jsx`: Visualizador de carta
- `Editorfinal.jsx`: Editor de manuscrito con tracking de cambios

**Componentes Reutilizables**:
- `components/bible/`: Secciones de Biblia (IdentidadObra, ArcoNarrativo, etc.)
- `components/dashboard/`: Tarjetas de proyecto
- `components/editor/`: Componentes del editor (ChangesList, SideBySideView)
- `components/ui/`: Botones, inputs, modales, spinners

### 6.3. Servicios API (api.js)

**Estructura modular**:
```javascript
const API_BASE = import.meta.env.VITE_API_URL

const authAPI = {
  login: async (password) => POST('/auth/login', {password}),
  logout: () => localStorage.removeItem('auth_token'),
  isAuthenticated: () => !!localStorage.getItem('auth_token'),
  getToken: () => localStorage.getItem('auth_token')
}

const projectsAPI = {
  getAll: async () => GET('/projects'),
  getById: async (id) => GET(`/project/${id}`),
  getStatus: async (id) => GET(`/project/${id}/status`),
  terminate: async (id) => POST(`/project/${id}/terminate`),
  delete: async (id) => DELETE(`/project/${id}`)
}

const bibleAPI = {
  get: async (id) => GET(`/project/${id}/bible`),
  save: async (id, bible) => POST(`/project/${id}/bible`, bible),
  approve: async (id) => POST(`/project/${id}/bible/approve`)
}

const manuscriptAPI = {
  getEdited: async (id) => GET(`/project/${id}/manuscript/edited`),
  getChanges: async (id) => GET(`/project/${id}/changes`),
  saveChangeDecision: async (id, changeId, decision) =>
    POST(`/project/${id}/changes/${changeId}/decision`, {decision}),
  export: async (id, decisions) =>
    POST(`/project/${id}/export`, {decisions})
}
```

**Interceptores de autenticación**:
```javascript
const fetchWithAuth = async (url, options) => {
  const token = authAPI.getToken()
  const response = await fetch(API_BASE + url, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  })

  if (response.status === 401) {
    authAPI.logout()
    window.location.href = '/login'
  }

  return response
}
```

---

## 7. Endpoints HTTP (API_DURABLE/HttpTriggers)

### 7.1. Autenticación

**POST /auth/login**
```json
Request: {"password": "secret"}
Response: {
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "Login successful"
}
```

### 7.2. Proyectos

**GET /projects**
```json
Response: [
  {
    "job_id": "Ana_20251211_045613",
    "book_name": "Ana",
    "status": "completed",
    "created_at": "2025-12-11T04:56:13Z"
  }
]
```

**GET /project/{id}/status**
```json
Response: {
  "instanceId": "Ana_20251211_045613",
  "runtimeStatus": "Running",
  "customStatus": {
    "phase": 6,
    "description": "Creating Bible",
    "progress": "50%"
  },
  "createdTime": "2025-12-11T04:56:13Z",
  "lastUpdatedTime": "2025-12-11T05:15:42Z"
}
```

### 7.3. Upload y Start

**POST /project/upload**
```
Content-Type: multipart/form-data

Files: manuscript.docx
Body: {
  "book_name": "Ana"
}

Response: {
  "job_id": "Ana_20251211_045613",
  "blob_path": "Ana_20251211_045613/Ana.docx",
  "message": "File uploaded successfully"
}
```

**POST /api/HttpStart**
```json
Request: {
  "job_id": "Ana_20251211_045613",
  "blob_path": "Ana_20251211_045613/Ana.docx",
  "book_name": "Ana"
}

Response: {
  "id": "Ana_20251211_045613",
  "statusQueryGetUri": "https://.../status?...",
  "sendEventPostUri": "https://.../raiseEvent/{eventName}?...",
  "terminatePostUri": "https://.../terminate?...",
  "purgeHistoryDeleteUri": "https://.../purgeHistory?..."
}
```

### 7.4. Biblia

**GET /project/{id}/bible**
```json
Response: {
  "identidad_obra": {...},
  "arco_narrativo": {...},
  "reparto_completo": [...],
  "voz_autor": {...},
  // ...
}
```

**POST /project/{id}/bible**
```json
Request: {
  "identidad_obra": {...},
  // Biblia editada completa
}

Response: {
  "message": "Bible saved successfully"
}
```

**POST /project/{id}/bible/approve**
```json
Response: {
  "message": "Bible approved, processing resumed"
}
```

### 7.5. Resultados

**GET /project/{id}/editorial-letter**
```json
Response: {
  "content": "Estimada Ana,\n\nHa sido un verdadero...",
  "metadata": {
    "length_chars": 3245,
    "length_words": 542
  }
}
```

**GET /project/{id}/manuscript/edited**
```
Response: "Capítulo 1\n\nAna no alcanzó a reaccionar. El golpe..."
```

**GET /project/{id}/changes**
```json
Response: [
  {
    "change_id": "ch1-change-000",
    "chapter_id": 1,
    "tipo": "redundancia",
    "original": "Ana no alcanzó a reaccionar a tiempo.",
    "editado": "Ana no alcanzó a reaccionar.",
    "justificacion": "...",
    "impacto_narrativo": "bajo",
    "status": "accepted",
    "position": {...}
  }
]
```

**POST /project/{id}/changes/{change_id}/decision**
```json
Request: {"decision": "rejected"}
Response: {"message": "Decision saved"}
```

**POST /project/{id}/export**
```json
Request: {
  "decisions": {
    "ch1-change-000": "accepted",
    "ch1-change-001": "rejected"
  }
}

Response: {
  "download_url": "https://.../Ana_Editado_Final.docx"
}
```

---

## 8. Gestión de Errores y Resiliencia

### 8.1. Reintentos con Tenacity

Todas las llamadas a APIs externas usan el decorador `@retry`:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=90)
)
def call_gemini_api(payload):
    response = requests.post(GEMINI_URL, json=payload)
    response.raise_for_status()
    return response.json()
```

**Estrategia**:
- 3 intentos máximo
- Backoff exponencial: 4s → 8s → 16s... hasta 90s max
- Reintentos ante: Network errors, 429 Rate Limit, 500 Server Errors

### 8.2. Fallback en Batch API

Si un batch falla parcialmente:

```python
# Identificar fragmentos faltantes
failed_fragments = [f for f in fragments if f["fragment_id"] not in results]

# Rescate individual (máximo 10 para no saturar)
rescued_results = []
for fragment in failed_fragments[:10]:
    try:
        result = analyze_chapter_individual(fragment)
        rescued_results.append(result)
    except Exception as e:
        logging.error(f"Failed to rescue fragment {fragment['fragment_id']}: {e}")
```

**Garantiza**: No se pierden análisis críticos por fallos transitorios.

### 8.3. Validación de JSON

Todas las respuestas de IA se validan:

```python
def safe_json_parse(response_text):
    try:
        # Limpiar markdown
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]

        return json.loads(clean_text)
    except json.JSONDecodeError:
        logging.error(f"Failed to parse JSON: {response_text[:200]}")
        return None  # Fallback a valores default
```

### 8.4. Manejo de Contenido Vacío

```python
# Ignorar fragmentos demasiado cortos (headers vacíos)
if len(fragment["content"]) < 100:
    logging.warning(f"Skipping empty fragment: {fragment['fragment_id']}")
    continue

# Sanitización de contenido editado
def sanitize_edited_content(content):
    # Eliminar preámbulos de IA
    content = re.sub(r"^(Aquí está|Here is).*?:\n", "", content)
    # Eliminar bloques de código
    content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
    return content.strip()
```

### 8.5. Logging Detallado

```python
import logging
import azure.functions.durable_functions as df

logging.info(f"[Phase 1] Starting manuscript segmentation for {job_id}")
start_time = time.time()

fragments = segment_book(blob_path)

elapsed = time.time() - start_time
logging.info(f"[Phase 1] Completed: {len(fragments)} fragments in {elapsed:.2f}s")
```

Azure Application Insights captura todos los logs con:
- Timestamp
- Severity (INFO/WARNING/ERROR)
- Orchestration Instance ID
- Custom properties

---

## 9. Costos y Performance

### 9.1. Estimación de Costos por Libro

**Libro típico**: 50,000 palabras, 20 capítulos

| Fase | Servicio | Tokens (aprox) | Costo |
|------|----------|---------------|-------|
| 2 - Análisis Factual | Gemini Flash Batch | ~100k input, 50k output | $0.15 |
| 4+5 - Estructural/Cualitativo | Gemini Pro Batch | ~150k input, 80k output | $0.60 |
| 6 - Biblia | Gemini Pro | ~80k input, 10k output | $0.25 |
| 7 - Carta Editorial | Gemini Pro | ~100k input, 5k output | $0.30 |
| 8 - Notas de Margen | Claude 3.7 Sonnet Batch | ~200k input, 40k output | $1.20 |
| 9 - Arcos | Gemini Pro Batch | ~150k input, 30k output | $0.45 |
| 10 - Edición | Claude 3.7 Sonnet Batch | ~300k input, 150k output | $2.50 |
| Azure Functions Compute | - | - | $0.15 |
| Azure Blob Storage | - | - | $0.02 |
| **TOTAL** | | | **~$5.62** |

**Nota**: Costos varían según longitud del manuscrito y complejidad del análisis.

### 9.2. Tiempos de Procesamiento

**Libro típico**: 50,000 palabras, 20 capítulos

| Fase | Tiempo Estimado |
|------|----------------|
| 1 - Segmentación | 5-10s |
| 2 - Capa 1 (Batch) | 2-5 min |
| 3 - Consolidación | 10-15s |
| 4+5 - Capas 2+3 (Paralelo) | 5-8 min |
| 6 - Biblia | 30-60s |
| **PAUSA HUMANA** | Variable |
| 7 - Carta Editorial | 60-90s |
| 8 - Notas (Claude Batch) | 10-15 min |
| 9 - Arcos (Gemini Batch) | 3-5 min |
| 10 - Edición (Claude Batch) | 15-20 min |
| 11 - Reconstrucción | 20-30s |
| 12 - Guardado | 10-15s |
| **TOTAL (sin pausa)** | **35-50 min** |

### 9.3. Comparación con Edición Humana

| Aspecto | LYA | Editor Humano |
|---------|-----|---------------|
| Costo | ~$6 | $2,000-$10,000 |
| Tiempo | 35-50 min + revisión humana | 2-6 semanas |
| Consistencia | Alta (mismos criterios siempre) | Variable (depende del editor) |
| Profundidad | Análisis multi-capa exhaustivo | Depende del nivel del editor |
| Preservación de voz | Muy alta (NO_CORREGIR explícito) | Variable |
| Creatividad | Baja (no reescribe creativamente) | Alta (puede sugerir giros) |
| Feedback pedagógico | Alto (explica cada cambio) | Variable |

**Conclusión**: LYA no reemplaza a editores senior, pero democratiza el acceso a retroalimentación editorial de calidad para el 95% de autores que no pueden costear servicios profesionales.

---

## 10. Limitaciones y Roadmap Futuro

### 10.1. Limitaciones Actuales

**Técnicas**:
- Solo soporta .docx (no PDF, ePub, TXT)
- Límite práctico de ~100k palabras (Azure Functions timeout de 10 min)
- Optimizado para español (funciona en inglés pero sin ajustes específicos)
- Requiere conexión estable a internet (no offline)

**De Negocio**:
- Costo de ~$6 por libro puede ser prohibitivo para uso iterativo frecuente
- Aprobación de Biblia requiere intervención humana (no fully automated)
- No soporta colaboración multi-usuario en tiempo real

**De Contenido**:
- Mejor rendimiento en ficción narrativa (novelas, cuentos)
- Rendimiento limitado en: Poesía, teatro, ensayo académico, no-ficción técnica
- No hace fact-checking de información histórica/científica
- No detecta plagio o similitudes con obras publicadas

### 10.2. Roadmap Potencial

**Corto Plazo (3-6 meses)**:
- Soporte para PDF y ePub
- Exportación a formato Scrivener
- Modo "Quick Edit" (solo Capa 1 + Edición básica, sin Biblia/Carta, ~10 min, $1.50)
- Dashboard de métricas (comparar Draft 1 vs Draft 2 vs Draft 3)
- Integración con Google Docs (plugin para editar directamente)

**Mediano Plazo (6-12 meses)**:
- Análisis de comparación entre versiones (mostrar evolución de scores)
- Sugerencias de estructura (reordenar capítulos, eliminar/añadir escenas)
- Detección de plot holes con IA especializada
- Generación de sinopsis y query letters
- Biblioteca de "estilos de autor" (emular a Stephen King, Brandon Sanderson, etc.)

**Largo Plazo (12+ meses)**:
- Editor colaborativo en tiempo real (múltiples usuarios editando simultáneamente)
- Análisis de "marketability" (predicción de éxito comercial basado en tendencias)
- Generación de primeros capítulos basados en outline (AI co-writing)
- Integración con plataformas de autopublicación (Amazon KDP, Wattpad)
- Modelo de subscripción (ediciones ilimitadas por $X/mes)

---

## 11. Casos de Uso y Audiencia

### 11.1. Target Users

**Autores Noveles**:
- Necesitan retroalimentación profesional antes de buscar agente/editor
- No pueden costear $3,000-$5,000 de developmental editing
- Quieren entender qué está funcionando y qué no en su manuscrito

**Autores Autopublicados**:
- Buscan calidad editorial sin depender de editoriales tradicionales
- Iteran múltiples borradores antes de publicar
- Valoran control total sobre cambios (accept/reject)

**Editores Freelance**:
- Usan LYA como primer pase antes de edición manual
- Ahorra 50-70% de tiempo en análisis estructural
- Se enfocan en creatividad y decisiones de alto nivel

**Escritores de Fan Fiction**:
- Quieren mejorar calidad narrativa
- Comunidad valora feedback constructivo
- Presupuesto limitado

**Estudiantes de Escritura Creativa**:
- Herramienta pedagógica (aprenden de las justificaciones de cada cambio)
- Practican con múltiples borradores
- Complemento a talleres y clases

### 11.2. Tipos de Manuscritos Soportados

**Ficción Narrativa** (mejor rendimiento):
- Fantasía (épica, urbana, oscura)
- Ciencia ficción (space opera, cyberpunk, distopía)
- Thriller/Misterio
- Romance (contemporáneo, histórico, paranormal)
- Young Adult (cualquier género)
- Literary Fiction
- Horror

**Soportado pero con limitaciones**:
- Cuentos cortos (>5k palabras recomendado)
- Novellas
- Antologías (procesar cada cuento por separado)

**No recomendado**:
- Poesía (requiere análisis de métrica/rima)
- Teatro (formato de diálogo puro)
- Ensayo académico (lógica argumentativa distinta)
- No-ficción técnica (requiere fact-checking)
- Libros infantiles ilustrados (dependen de imágenes)

---

## 12. Conclusiones

### 12.1. Fortalezas del Proyecto

**Análisis Multi-Capa Sofisticado**:
- Combina análisis factual, estructural, cualitativo y causal
- Profundidad comparable a editor humano experimentado
- Cobertura exhaustiva (100% del manuscrito analizado)

**Biblia Narrativa como Fuente de Verdad**:
- Garantiza consistencia en todas las decisiones editoriales
- Previene sobrecorrección mediante NO_CORREGIR explícito
- Define identidad de la obra de manera holística

**Edición Respetuosa de la Voz Autoral**:
- No reescribe creativamente (solo corrige problemas técnicos)
- Preserva estilo distintivo del autor
- Cambios quirúrgicos con justificación pedagógica

**Tracking de Cambios Granular**:
- Cada edición rastreable con contexto antes/después
- Capacidad de aceptar/rechazar cambios individuales
- Exportación de versión final personalizada

**Arquitectura Escalable y Resiliente**:
- Durable Functions permite workflows complejos sin mantener estado manual
- Reintentos automáticos y fallbacks previenen pérdidas de datos
- Polling adaptativo optimiza latencia y costo

**Optimizaciones de Performance**:
- Batch APIs reducen tiempo 70% vs llamadas secuenciales
- Paralelización de fases independientes ahorra 40% en capas 4+5
- Polling adaptativo equilibra UX y costo de APIs

### 12.2. Innovación Central

LYA representa un **enfoque híbrido único**:

**Velocidad y escala de automatización** (35-50 minutos vs 2-6 semanas) +
**Sensibilidad editorial humana** (respeto a voz, crítica constructiva, priorización)

No intenta **reemplazar** editores humanos senior (que aportan creatividad, experiencia de mercado y conexión humana), sino **democratizar el acceso** a retroalimentación editorial de calidad profesional para:
- Autores que no pueden costear $2,000-$10,000 por manuscrito
- Iteraciones tempranas de borradores (Draft 1, 2, 3)
- Autores en mercados emergentes (Latinoamérica, Asia, África)

### 12.3. Impacto Potencial

**Reducción de barreras de entrada**:
- De $5,000 a $6 por manuscrito = 833x más accesible
- Retroalimentación en horas vs semanas = 100x más rápido

**Mejora de calidad global de literatura autopublicada**:
- Autores aprenden de justificaciones pedagógicas
- Iteran más veces antes de publicar
- Elevan estándares de calidad

**Empoderamiento de autores**:
- Control total sobre cambios (no imposición editorial)
- Transparencia completa (cada cambio explicado)
- Preservación de voz autoral única

---

## 13. Archivos Clave del Proyecto

### Backend (Lógica de Negocio)

| Archivo | Propósito |
|---------|-----------|
| `API_DURABLE/Orchestrator/__init__.py` | Orquestador principal (12 fases) |
| `API_DURABLE/SegmentBook/__init__.py` | Segmentación de manuscritos |
| `API_DURABLE/ConsolidateFragmentAnalyses/__init__.py` | Fusión de fragmentos en capítulos |
| `API_DURABLE/CreateBible/__init__.py` | Generación de Biblia Narrativa |
| `API_DURABLE/GenerateEditorialLetter/__init__.py` | Carta editorial |
| `API_DURABLE/SubmitClaudeBatch/__init__.py` | Edición profesional (prompt) |
| `API_DURABLE/ReconstructManuscript/__init__.py` | Ensamblaje final de manuscritos |
| `API_DURABLE/HttpTriggers/__init__.py` | Endpoints HTTP |

### Frontend (Interfaz de Usuario)

| Archivo | Propósito |
|---------|-----------|
| `CLIENT/src/App.jsx` | Router principal y rutas |
| `CLIENT/src/services/api.js` | Cliente HTTP con módulos API |
| `CLIENT/src/pages/Upload.jsx` | Subida de manuscritos |
| `CLIENT/src/pages/ProjectStatus.jsx` | Monitoreo de progreso con polling |
| `CLIENT/src/pages/BibleReview.jsx` | Revisión y aprobación de Biblia |
| `CLIENT/src/pages/Editorfinal.jsx` | Editor de manuscritos con tracking |

### Outputs (Ejemplos Reales)

| Archivo | Propósito |
|---------|-----------|
| `outputs/metadata.json` | Info del proyecto |
| `outputs/biblia_validada.json` | Biblia Narrativa completa |
| `outputs/carta_editorial.md` | Carta editorial en markdown |
| `outputs/cambios_estructurados.json` | Tracking de cambios |
| `outputs/notas_margen.json` | Notas de margen por capítulo |
| `outputs/resumen_ejecutivo.json` | Índice de todos los archivos + estadísticas |

---

## Apéndice: Ejemplo Real de Procesamiento

### Manuscrito: Ana.docx

**Metadata**:
- Palabras: ~12,000
- Capítulos: 3
- Género detectado: Fantasía Oscura (Grimdark)
- Tiempo de procesamiento: ~30 minutos

**Biblia Generada**:
```json
{
  "identidad_obra": {
    "genero": "Fantasía Oscura (Grimdark)",
    "tono": "Visceral, opresivo, sensorial y sombrío",
    "tema_central": "La fragilidad humana frente a la crueldad",
    "estilo_narrativo": "TERCERA_LIMITADA"
  },
  "voz_autor": {
    "estilo": "POETICO",
    "NO_CORREGIR": [
      "Término 'Cuernomuro' (worldbuilding)",
      "Uso de 'cobertijo' (regionalismo intencional)",
      "Descripciones explícitas de violencia (tono grimdark)"
    ]
  },
  "problemas_priorizados": [
    {
      "tipo": "DISTANCIA_PSIQUICA",
      "severidad": "CRITICA",
      "descripcion": "Falta de acceso a pensamientos internos de Ana"
    },
    {
      "tipo": "RITMO_REPETITIVO",
      "severidad": "MEDIA",
      "descripcion": "Estructura similar en los 3 capítulos"
    }
  ]
}
```

**Carta Editorial** (fragmento):
> "Estimada Ana,
> Ha sido un verdadero privilegio sumergirme en el borrador de tu novela. Desde las primeras líneas, queda claro que no tienes miedo de llevar al lector a lugares oscuros, incómodos y profundamente humanos. Tu manuscrito posee una cualidad visceral que es rara de encontrar en los primeros borradores, y tu capacidad para construir atmósfera mediante detalles sensoriales es notable.
>
> Entre las fortalezas principales, destaco tu worldbuilding implícito. Cuernomuro emerge como un lugar palpable sin necesidad de largos párrafos expositivos..."

**Cambios Aplicados**: 42 total
- Redundancias: 12
- Show vs Tell: 13
- Consistencia: 1
- Transiciones: 3
- Emoción: 3
- Otros: 10

**Notas de Margen**: 35 total distribuidas en 3 capítulos

---

**FIN DEL DOCUMENTO**

---

*Este documento describe LYA v5.3. Para actualizaciones, consultar el repositorio oficial.*
