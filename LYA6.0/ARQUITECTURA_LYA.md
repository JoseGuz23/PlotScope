# LYA: Sistema de Edición Editorial Profesional Impulsado por IA

## Documento de Arquitectura y Funcionamiento

**Versión**: 6.0 "Editor Reflexivo"
**Fecha**: Diciembre 2025
**Proyecto**: LYA (anteriormente Sylphrena)

---

## 1. ¿Qué es LYA?

LYA es un **sistema de edición editorial profesional automatizado con capacidades de auto-crítica y reflexión iterativa** que funciona como un *Developmental Editor* virtual. Toma manuscritos literarios en formato DOCX y produce retroalimentación editorial de calidad profesional comparable a la que proporcionaría un editor humano experimentado.

### Propósito Central

Democratizar el acceso a edición editorial de calidad para autores que no pueden costear servicios profesionales tradicionales (que típicamente oscilan entre $2,000-$10,000 USD por manuscrito).

### Productos Finales que Genera

Cuando un autor sube su manuscrito, LYA produce:

1. **Biblia Narrativa**: Documento maestro con la identidad completa de la obra (género, tono, tema, arcos de personajes, voz autoral, mapas de ritmo, **arco emocional**, problemas priorizados)

2. **Carta Editorial Profesional**: Documento de 1,500-2,500 palabras escrito en prosa natural que imita el tono de un editor real, con fortalezas, debilidades y plan de acción

3. **Notas al Margen**: Comentarios críticos párrafo por párrafo sobre claridad, show-vs-tell (con **análisis sensorial cuantitativo**), ritmo, tensión y consistencia

4. **Manuscrito Editado**: Versión corregida del texto con cambios aplicados mediante **reflection loops** (redundancias eliminadas, show-vs-tell mejorado, ritmo variado, con auto-crítica y refinamiento iterativo)

5. **Manuscrito Anotado**: Versión con cambios resaltados y explicaciones de cada corrección

6. **Tracking de Cambios**: Base de datos estructurada de cada edición realizada, con justificación, impacto narrativo, **estadísticas de reflection** y capacidad de aceptar/rechazar cambios

---

## 2. Arquitectura General del Sistema

### Componentes Principales

LYA está construido sobre **dos pilares arquitectónicos**:

#### **API_DURABLE** (Backend - Azure Durable Functions)
Motor de procesamiento basado en orquestación serverless que coordina **14 fases** de análisis y edición secuenciales. Utiliza Azure Durable Functions para mantener estado complejo a través de workflows de larga duración (45-65 minutos por libro).

**Tecnologías core**:
- Python 3.9+
- Azure Durable Functions (pattern: Function Chaining + Human Interaction)
- Azure Blob Storage (persistencia de manuscritos y resultados)
- Google Gemini 2.5 API (análisis estructural, cualitativo, síntesis y crítica)
- Anthropic Claude 4.5 API (edición de prosa y notas críticas)
- **HuggingFace Transformers** (sentiment analysis local)
- **Context Caching** (optimización de costos)

#### **CLIENT** (Frontend - React Web Application)
Interfaz de usuario moderna para subir manuscritos, monitorear progreso, revisar la Biblia Narrativa, **visualizar insights emocionales y sensoriales** y trabajar con resultados.

**Tecnologías core**:
- React 19 + React Router 7
- Vite (bundler experimental con rolldown)
- TailwindCSS 4
- TipTap (editor WYSIWYG)
- docx.js (generación de archivos Word)
- **Visualizaciones de arco emocional y métricas de showing**

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
│  - Visualización de arco emocional (NUEVO v6.0)        │
│  - Métricas de Show vs Tell (NUEVO v6.0)               │
│  - Editor de manuscritos con tracking de cambios       │
│  - Reflection stats por capítulo (NUEVO v6.0)          │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS/REST API
                       ▼
┌─────────────────────────────────────────────────────────┐
│         BACKEND (Azure Durable Functions)               │
│                                                         │
│  ┌───────────────────────────────────────────────┐      │
│  │      Orchestrator (14 Fases Secuenciales)     │      │
│  │   + 2 Fases Nuevas: Emocional + Sensorial     │      │
│  └───────────────────────────────────────────────┘      │
│                       │                                 │
│         ┌─────────────┼─────────────┐                   │
│         ▼             ▼             ▼                   │
│   ┌─────────┐  ┌──────────┐  ┌──────────┐               │
│   │ Gemini  │  │  Claude  │  │  Azure   │               │
│   │  2.5    │  │   4.5    │  │  Blob    │               │
│   └─────────┘  └──────────┘  └──────────┘               │
│   (Análisis +  (Edición +    (Storage +                 │
│    Crítica)     Reflection)   Context Cache)            │
│                                                         │
│   ┌──────────────────────────────────┐                  │
│   │  NUEVO v6.0: Reflection Loops    │                  │
│   │  Crítico ↔ Refinador (3 iter)    │                  │
│   └──────────────────────────────────┘                  │
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
    → [NUEVO v6.0] Análisis de arco emocional (sentiment analysis)
    → [NUEVO v6.0] Detección sensorial para Show vs Tell
    → Síntesis en Biblia Narrativa (incluye insights emocionales)
    → [APROBACIÓN HUMANA]
    → Generación de carta editorial
    → [NUEVO v6.0] Edición con Reflection Loops selectivos
    → Reconstrucción de manuscrito editado
    → Entrega de paquete completo
```

### Las 14 Fases del Orquestador (v6.0)

El orquestador de Durable Functions ejecuta 14 fases secuenciales, cada una construyendo sobre los resultados anteriores:

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

**Tiempo estimado**: 5-10 segundos.

---

#### **FASE 2: Análisis Factual (Capa 1) - Batch API**

**Objetivo**: Extraer hechos objetivos de cada fragmento (personajes, eventos, métricas).

**Proceso**:
- Envía TODOS los fragmentos en un único batch a Google Gemini Batch API
- Utiliza el modelo **`gemini-2.5-flash`** (actualizado desde v5.3, mejor razonamiento)
- Para cada fragmento, el modelo extrae:
  - **Personajes**: Protagonistas, antagonistas, secundarios con roles y características
  - **Secuencia de eventos**: Cronología de lo que ocurre en el fragmento
  - **Métricas básicas**: Total de palabras, párrafos, porcentaje de diálogo, ritmo estimado
  - **Señales tempranas de edición**: Problemas evidentes detectados
- Polling adaptativo: Consulta el estado del batch con intervalos crecientes (10s → 15s → 20s... hasta 45s max)
- Si algunos fragmentos fallan, aplica rescate individual usando llamadas directas

**Tecnología**: Google Gemini 2.5 Flash Batch API con polling adaptativo implementado mediante `time.sleep()` con intervalos calculados dinámicamente.

**Salida**: Lista de análisis factuales por fragmento en formato JSON estructurado.

**Optimización clave**: Batch API reduce de 20 llamadas secuenciales (20+ minutos) a 1 llamada paralela (~2-5 minutos).

**Tiempo estimado**: 2-5 minutos.

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

**Tiempo estimado**: 10-15 segundos.

---

#### **FASES 4+5: Análisis Paralelo (Capas 2 y 3)**

**Objetivo**: Profundizar el análisis con perspectivas estructurales y cualitativas en paralelo.

**Proceso de Paralelización**:
- Usa `context.task_all([submit_layer2, submit_layer3])` de Durable Functions para ejecutar ambas fases simultáneamente
- Ambas envían batches independientes a Gemini Pro 2.5
- Polling paralelo hasta que ambos completen

##### **CAPA 2 - Análisis Estructural**
**Motor**: Google Gemini Pro 2.5 (`gemini-2.5-pro`, actualizado desde v5.3)

Analiza por cada capítulo:
- **Componentes narrativos**: Exposición, conflicto, clímax, resolución (estructura clásica)
- **Dinámica de escenas**: Proporción de acción/diálogo/reflexión
- **Arcos de personajes detectados**: Cambios emocionales y de objetivo
- **Hooks y payoffs**: Setups abiertos (promesas narrativas) y resoluciones cumplidas
- **Score estructural**: Evaluación de qué tan bien estructurado está el capítulo (0-10)

##### **CAPA 3 - Análisis Cualitativo**
**Motor**: Google Gemini Pro 2.5

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

**Tiempo estimado**: 5-8 minutos (paralelo).

---

#### **FASE 5.5: Análisis de Arco Emocional** ✨ NUEVO v6.0

**Objetivo**: Detectar el "latido emocional" del manuscrito mediante sentiment analysis.

**Motor**: HuggingFace Transformers + modelo `finiteautomata/beto-sentiment-analysis` (español)

**Proceso**:
1. Divide cada capítulo en ventanas deslizantes de 500 palabras
2. Analiza sentimiento de cada ventana usando modelo ML local
3. Genera valencia emocional (-1.0 negativo a +1.0 positivo) por ventana
4. Detecta patrón emocional del capítulo:
   - **ASCENDENTE**: Esperanzador (coming-of-age)
   - **DESCENDENTE**: Trágico (grimdark)
   - **MONTAÑA_RUSA**: Thriller/acción
   - **VALLE**: Estructura clásica (3 actos)
   - **PLANO_NEGATIVO**: Grimdark sostenido
   - **PLANO_POSITIVO**: Romance ligero
5. Identifica momentos críticos (picos positivos, valles negativos)
6. Genera diagnósticos automáticos (ej: "Capítulo 5 muy plano, añadir contraste")

**Output Ejemplo**:
```json
{
  "chapter_id": 1,
  "emotional_trajectory": [
    {"window_index": 0, "valence": -0.45, "label": "NEG"},
    {"window_index": 1, "valence": -0.30, "label": "NEG"},
    {"window_index": 2, "valence": 0.10, "label": "NEU"},
    {"window_index": 3, "valence": 0.65, "label": "POS"}
  ],
  "avg_valence": -0.15,
  "emotional_range": 1.10,
  "emotional_pattern": "ASCENDENTE",
  "critical_moments": [
    {
      "type": "PICO_POSITIVO",
      "window_index": 3,
      "valence": 0.65,
      "description": "Momento de mayor intensidad emocional positiva"
    }
  ]
}
```

**Integración**: Los arcos emocionales se añaden a la Biblia Narrativa en la sección `mapa_ritmo`.

**Tiempo estimado**: 60-90 segundos.

---

#### **FASE 5.6: Detección Sensorial para Show vs Tell** ✨ NUEVO v6.0

**Objetivo**: Análisis cuantitativo de contenido sensorial vs abstracto párrafo por párrafo.

**Motor**: Análisis léxico con léxicos sensoriales catalogados (200+ palabras)

**Léxicos Implementados**:
- **Visual**: 50+ palabras (colores, formas, verbos visuales: "brillar", "oscuro", "rojo")
- **Auditivo**: 30+ palabras (sonidos: "crujir", "susurrar", "retumbar")
- **Olfativo**: 15+ palabras (olores: "hedor", "fragancia", "rancio")
- **Táctil**: 40+ palabras (texturas, temperatura: "áspero", "frío", "viscoso")
- **Gustativo**: 12+ palabras (sabores: "amargo", "dulce", "ácido")
- **Kinestésico**: 25+ palabras (movimiento corporal: "temblar", "arrastrarse")

**Marcadores Abstractos** (para detectar "telling"):
- Emociones directamente nombradas: "miedo", "tristeza", "alegría"
- Estados mentales: "pensar", "creer", "saber"
- Conceptos abstractos: "destino", "esperanza", "honor"

**Proceso**:
1. Divide cada capítulo en párrafos
2. Por cada párrafo:
   - Cuenta palabras sensoriales por categoría
   - Cuenta marcadores abstractos
   - Calcula `sensory_density` = sensory_words / total_words
   - Calcula `abstract_density` = abstract_words / total_words
3. Clasifica párrafo:
   - **SHOWING**: `sensory_density > 0.15` AND `abstract_density < 0.1`
   - **TELLING**: `abstract_density > 0.15`
   - **VAGO**: `sensory_density < 0.1`
4. Genera diagnóstico por párrafo y capítulo

**Output Ejemplo**:

❌ **Telling** (densidad sensorial: 0.05):
```
Ana sintió miedo. El valle era aterrador.
```

✅ **Showing** (densidad sensorial: 0.35):
```
El aire olía a grasa rancia. Ana sintió cómo los dedos se le
entumecían por el frío. El pelaje áspero de la bestia rozó su mejilla.
```

**Integración**: Los datos sensoriales se inyectan en los capítulos consolidados y se usan en Notas de Margen para sugerencias específicas.

**Tiempo estimado**: 60-90 segundos.

---

#### **FASE 6: Creación de la Biblia Narrativa**

**Objetivo**: Sintetizar TODO el conocimiento adquirido en un documento maestro que define la identidad de la obra.

**Motor**: Google Gemini Pro 2.5 con JSON Schema estricto.

**Inputs que consume**:
- Capítulos consolidados (con Capas 1, 2 y 3)
- **Arcos emocionales** (Fase 5.5) ✨ NUEVO
- **Análisis sensorial** (Fase 5.6) ✨ NUEVO
- Análisis holístico previo (lectura rápida del manuscrito completo)
- Metadata del libro

**Estructura de la Biblia Generada** (actualizada v6.0):

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
    "patron_emocional_global": "VALLE",
    "avg_valence_global": -0.15,
    "ritmo_por_capitulo": [
      {
        "chapter_id": 1,
        "ritmo": "LENTO",
        "razon": "Establecimiento de atmósfera",
        "arco_emocional": {
          "avg_valence": -0.45,
          "pattern": "PLANO_NEGATIVO",
          "emotional_range": 0.25
        },
        "sensory_metrics": {
          "showing_ratio": 0.47,
          "avg_sensory_density": 0.18
        }
      }
    ]
  },

  "problemas_priorizados": [
    {
      "tipo": "DISTANCIA_PSIQUICA",
      "severidad": "CRITICA",
      "descripcion": "Falta de acceso a pensamientos de Ana",
      "capitulos_afectados": [1, 2, 3],
      "sugerencia": "Intercalar monólogo interior"
    },
    {
      "tipo": "EXCESO_TELLING",
      "severidad": "ALTA",
      "descripcion": "Capítulo 3 tiene solo 25% de showing",
      "capitulos_afectados": [3],
      "sugerencia": "Convertir emociones nombradas en sensaciones físicas",
      "sensory_data": {
        "showing_ratio": 0.25,
        "problem_paragraphs": 8
      }
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
    "score_global": 8.1,
    "showing_ratio_promedio": 0.47,
    "valencia_emocional_promedio": -0.15
  }
}
```

**Función crítica**: La Biblia es la **fuente de verdad** para todas las fases siguientes. Define:
- Qué NO debe corregirse (elementos estilísticos intencionales)
- Voz autoral a preservar
- Problemas priorizados a atacar (incluye métricas cuantitativas)
- Contexto narrativo para entender decisiones editoriales
- **Arco emocional esperado** ✨ NUEVO
- **Métricas de showing objetivo** ✨ NUEVO

**Salida**: Archivo JSON que se guarda en Blob Storage y se pasa a todas las fases posteriores.

**Tiempo estimado**: 30-60 segundos.

---

#### **PAUSA PARA APROBACIÓN HUMANA**

**Punto de control crítico**: El orquestador entra en modo de espera (`WaitForExternalEvent("BibleApproved")`).

**Flujo de aprobación**:
1. Usuario revisa la Biblia en la interfaz web (`BibleReview.jsx`)
2. **NUEVO v6.0**: Ve sección de "Ritmo Emocional" con arcos por capítulo
3. Puede editar secciones si la IA malinterpretó algo
4. Guarda cambios con `POST /project/{id}/bible`
5. Cuando aprueba: `POST /project/{id}/bible/approve` envía evento "BibleApproved"
6. El orquestador se reanuda y continúa con Fase 7

**Razón de ser**: La Biblia define decisiones editoriales fundamentales. Si la IA malinterpreta el género o el tono, todas las fases posteriores serán incorrectas. La aprobación humana garantiza que el análisis es preciso antes de invertir en edición costosa.

**Tiempo de pausa**: Variable (minutos a horas o días, según disponibilidad del autor).

---

#### **FASE 7: Generación de Carta Editorial**

**Objetivo**: Producir un documento en prosa natural que imite la carta que enviaría un editor profesional.

**Motor**: Google Gemini Pro 2.5 en modo texto plano (no JSON).

**Inputs**:
- Biblia Narrativa completa (incluye arcos emocionales)
- Capítulos consolidados (resumen)
- Fragmentos originales (contexto de problemas específicos)
- **Métricas de showing y arco emocional** ✨ NUEVO

**Estructura del Prompt**:
El prompt solicita explícitamente una carta de 1,500-2,500 palabras con estructura clásica de editorial letter:
- Saludo personal y primeras impresiones
- Fortalezas principales (3-5 párrafos con ejemplos específicos)
- Áreas de mejora (5-8 párrafos, problemas priorizados de mayor a menor severidad)
  - **NUEVO**: Incluye métricas cuantitativas de showing
  - **NUEVO**: Menciona patrones emocionales detectados
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

**Tiempo estimado**: 60-90 segundos.

---

#### **FASE 8: Generación de Notas al Margen (Claude Batch API)**

**Objetivo**: Crear comentarios críticos párrafo por párrafo como haría un editor humano al margen del manuscrito.

**Motor**: Anthropic Claude Sonnet 4.5 via Batch API (actualizado desde 3.7 Sonnet).

**Proceso**:
- Envía un batch con TODOS los capítulos
- Por cada capítulo, Claude recibe:
  - Contenido del capítulo
  - Carta editorial (para entender prioridades globales)
  - Biblia Narrativa (para contexto de voz y tono)
  - **Análisis sensorial del capítulo** ✨ NUEVO
  - Metadata del libro
- Claude genera notas críticas específicas con esta estructura:

```json
{
  "nota_id": "ch2-nota-001",
  "parrafo_aprox": 1,
  "texto_referencia": "El cuerpo de Ana no podía parar de temblar...",
  "tipo": "show_tell",
  "severidad": "alta",
  "nota": "Párrafo 3 tiene 'telling' excesivo (densidad abstracta: 0.20)",
  "sugerencia": "En lugar de 'Ana sintió miedo', describe: manos temblando, respiración acelerada, sudor frío. Objetivo: sensory_density > 0.15",
  "impacto_si_no_se_corrige": "El lector no sentirá la emoción, solo la leerá",
  "sensory_analysis": {
    "sensory_density": 0.05,
    "abstract_density": 0.20,
    "dominant_sense": "ninguno"
  }
}
```

**Tipos de notas**:
- `claridad`: Confusión sobre espacio/tiempo/eventos
- `show_tell`: Casos de "telling" que deberían ser "showing" (con datos cuantitativos)
- `ritmo`: Problemas de pacing (demasiado lento/rápido)
- `tension`: Falta de stakes o pérdida de engagement
- `personaje`: Inconsistencias o falta de desarrollo
- `voz`: Desviaciones del tono establecido
- `emocion`: Falta de coherencia con arco emocional esperado ✨ NUEVO

**Polling adaptativo**: Intervalos de 20s → 35s → 50s... hasta 90s max.

**Salida**: Diccionario de listas de notas organizadas por `chapter_id`.

**Tiempo estimado**: 10-15 minutos para libro de 20 capítulos.

**Razón de usar Claude 4.5**: Superior en crítica constructiva y explicaciones pedagógicas (vs Gemini que es mejor en análisis estructurado).

---

#### **FASE 9: Mapas de Arcos (Gemini Pro Batch)**

**Objetivo**: Crear guías de continuidad para que la edición no rompa elementos narrativos críticos.

**Motor**: Google Gemini Pro 2.5 Batch API.

**Análisis por capítulo**:
- **Elementos de worldbuilding introducidos**: Qué información nueva sobre el mundo se revela
- **Setups y payoffs**: Configuraciones abiertas (promesas) vs resoluciones logradas
- **Estado emocional de protagonistas**: Al inicio y final del capítulo (tracking de arco emocional)
- **Posición en estructura de 3 actos**: ¿En qué parte de la estructura está este capítulo?
- **Elementos críticos para continuidad**: Objetos, información, relaciones que NO pueden alterarse sin romper lógica
- **Notas para el editor**: Qué preservar absolutamente, qué puede revisarse

**Salida**: Diccionario de arc_maps por `chapter_id`.

**Razón de ser**: Previene que la edición automática rompa la lógica causal. Ejemplo: Si en capítulo 3 el personaje pierde una espada y en capítulo 5 la usa, el editor no puede eliminar la mención de pérdida.

**Tiempo estimado**: 3-5 minutos.

---

#### **FASE 10: Edición Profesional con Reflection Loops** ✨ NUEVO v6.0

**Objetivo**: Aplicar correcciones de prosa manteniendo la voz autoral y respetando la Biblia, con **auto-crítica y refinamiento iterativo**.

### ¿Qué son Reflection Loops?

En lugar de editar un capítulo una sola vez (single-pass), el sistema itera:

1. **Agente Redactor** (Claude Sonnet 4.5): Genera propuesta de edición
2. **Agente Crítico** (Gemini Pro 2.5): Evalúa con rigor extremo (score 0-10)
3. **Si score < 9.0**: Envía feedback al Redactor → Refinar → Repetir (max 3 iteraciones)
4. **Si score >= 9.0**: Aprobar y continuar

### Arquitectura del Bucle

```
┌─────────────────┐
│  Texto Original │
└────────┬────────┘
         │
         ▼
    ┌────────────────┐
    │ Agente Redactor│  (Claude Sonnet 4.5)
    │ (1ra iteración)│
    └────────┬───────┘
             │
             ▼
      ┌──────────────┐
      │ Agente Crítico│  (Gemini Pro 2.5)
      │  Evalúa (8.2) │
      └──────┬─────────┘
             │
             ▼ Score < 9.0?
        ┌──────────┐
        │ Refinador │  (Claude Sonnet 4.5 con feedback)
        │ (2da iter)│
        └────┬─────┘
             │
             ▼
      ┌──────────────┐
      │ Agente Crítico│
      │  Evalúa (9.3) │  ✅ APROBADO
      └──────────────┘
```

### Criterios de Evaluación del Crítico

1. **Preservación de voz autoral** (crítico) - Score 0-10
2. **Ausencia de alucinaciones** (crítico) - ¿Se añadió info no presente?
3. **Mejora real de Show vs Tell** (alto) - ¿Conversión a sensorial?
4. **Economía narrativa** (medio) - Redundancias eliminadas
5. **Coherencia con Biblia** (alto) - Respeta tono y género

### Implementación Selectiva (Ahorro de Costos)

```python
from config_models import REFLECTION_QUALITY_THRESHOLD

for chapter in chapters:
    qualitative_score = chapter['layer3_qualitative'].get('score_global', 10)

    if qualitative_score < REFLECTION_QUALITY_THRESHOLD:  # < 7.0
        # Capítulo problemático: usar reflection (3 iteraciones)
        edited = yield context.call_activity('ReflectionEditingLoop', {
            'chapter': chapter,
            'bible': bible,
            'margin_notes': margin_notes,
            ...
        })
    else:
        # Capítulo bueno: single-pass (1 iteración)
        edited = yield context.call_activity('SubmitClaudeBatch', {...})
```

**Resultado**: ~80% del beneficio a ~40% del costo adicional.

### Métricas de Reflection

```json
{
  "reflection_stats": {
    "iterations_used": 2,
    "first_score": 8.2,
    "final_score": 9.3,
    "improvement_delta": 1.1,
    "feedback_history": [
      {
        "score_global": 8.2,
        "aprobado": false,
        "fallos_criticos": [
          "Párrafo 3: Se cambió 'espada de hueso' por 'espada' (dato perdido)"
        ],
        "mejoras_requeridas": [
          "Restaurar 'de hueso' en descripción"
        ]
      },
      {
        "score_global": 9.3,
        "aprobado": true
      }
    ]
  }
}
```

### Inputs completos por capítulo (contexto masivo):

- Contenido del capítulo completo
- Biblia Narrativa (identidad, voz, NO_CORREGIR)
- Capítulos consolidados (contexto global del manuscrito)
- Mapa de arcos del capítulo (continuidad)
- Notas de margen (prioridades específicas)
- **Análisis sensorial** (objetivos cuantitativos de showing) ✨ NUEVO
- Metadata del libro

**Proceso de Claude**:
- Lee el capítulo completo con todo el contexto
- Identifica problemas según criterios
- Aplica correcciones quirúrgicas (no reescribe todo, solo corrige lo problemático)
- Documenta CADA cambio con justificación
- **Si es rechazado por el Crítico**: Refina basándose en feedback específico

**Salida**: Lista de fragmentos editados con:
- `contenido_editado`: Texto corregido
- `cambios_estructurados`: Lista de modificaciones con tipo, original/editado, justificación, impacto
- `reflection_stats`: Iteraciones usadas, scores, mejora lograda ✨ NUEVO

**Tiempo estimado**: 25-35 minutos para libro de 20 capítulos (vs 15-20 min en v5.3).

**Beneficio**: Reducción de alucinaciones de ~15% a ~5% (-70% errores).

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
  "reflection_iteration": 1,
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
   - **Estadísticas de reflection** (capítulos con iteraciones múltiples) ✨ NUEVO

**Salida**:
- `manuscripts`: {original, edited, annotated} en texto markdown
- `consolidated_chapters`: Capítulos con contenido editado inyectado
- `cambios_estructurados`: Lista completa de cambios
- `statistics`: Métricas agregadas (incluye reflection stats)

**Razón de ser**: Convierte ediciones fragmentadas en productos finales coherentes y proporciona tracking granular para aceptar/rechazar cambios.

**Tiempo estimado**: 20-30 segundos.

---

#### **FASE 12: Guardado de Resultados en Azure Blob Storage**

**Objetivo**: Persistir todos los artefactos generados en almacenamiento permanente.

**Proceso**:
Sube a Azure Blob Storage (container: `lya-outputs/{job_id}/`):

1. **metadata.json**: Info del proyecto
   - `job_id`, `book_name`, `version: "6.0"`, `created_at`, `status`
   - Counts (total de capítulos, fragmentos, cambios)
   - **Reflection stats agregadas** ✨ NUEVO

2. **biblia_validada.json**: Biblia Narrativa completa (con arcos emocionales)

3. **biblia_narrativa.md**: Versión en markdown legible de la Biblia

4. **carta_editorial.json**: Carta + metadata (longitud)

5. **carta_editorial.md**: Carta en markdown

6. **notas_margen.json**: Notas de margen organizadas por capítulo (con análisis sensorial)

7. **capitulos_consolidados.json**: Capítulos con todos los análisis (Capas 1/2/3, arcos, contenido editado, emocional, sensorial)

8. **cambios_estructurados.json**: Lista de cambios con decision tracking y reflection stats

9. **reporte_cambios.md**: Reporte legible de cambios en markdown

10. **emotional_arc_analysis.json**: Análisis emocional completo ✨ NUEVO

11. **sensory_detection_analysis.json**: Análisis sensorial completo ✨ NUEVO

12. **resumen_ejecutivo.json**: Índice de todos los archivos con URLs de Blob Storage + estadísticas

**Formato de URLs**:
```
https://lyastorage.blob.core.windows.net/lya-outputs/{job_id}/biblia_validada.json
```

**Respuesta final al cliente**:
```json
{
  "status": "completed",
  "job_id": "Ana_20251211_045613",
  "version": "6.0",
  "manuscripts": {
    "original": "texto original completo...",
    "edited": "texto editado completo...",
    "annotated": "texto anotado completo..."
  },
  "statistics": {
    "total_changes": 42,
    "changes_by_type": {...},
    "reflection_stats": {
      "chapters_with_reflection": 4,
      "avg_iterations": 1.4,
      "avg_improvement": 1.2
    },
    "emotional_arc": {
      "global_pattern": "VALLE",
      "avg_valence": -0.15
    },
    "sensory_metrics": {
      "global_showing_ratio": 0.47,
      "avg_sensory_density": 0.18
    }
  },
  "bible_url": "https://...",
  "carta_url": "https://...",
  "processing_time_seconds": 2847
}
```

**Tiempo estimado**: 10-15 segundos.

---

## 4. Tecnologías y Metodologías Clave

### 4.1. Azure Durable Functions

**Patrón arquitectónico**: Function Chaining + Human Interaction Pattern

**Razón de uso**:
- Workflows de larga duración (45-65 minutos) sin mantener servidor activo
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

    # NUEVO v6.0: Fases emocionales
    emotional = yield context.call_activity("EmotionalArcAnalysis", consolidated)
    sensory = yield context.call_activity("SensoryDetectionAnalysis", consolidated)

    # Espera aprobación humana
    bible_approved = yield context.wait_for_external_event("BibleApproved")

    # NUEVO v6.0: Edición con reflection
    for chapter in chapters:
        if chapter['score'] < 7.0:
            edited = yield context.call_activity('ReflectionEditingLoop', chapter)
        else:
            edited = yield context.call_activity('EditChapterSimple', chapter)

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

**Beneficio**: Reduce tiempo de 90+ minutos a 45-65 minutos.

### 4.3. División de Trabajo entre Gemini y Claude

**Google Gemini 2.5** (actualizado v6.0):
- Análisis estructurado (JSON schemas)
- Síntesis de información (Biblia)
- Análisis cuantitativo (scores, métricas)
- **Crítica en Reflection Loops** ✨ NUEVO
- Mayor ventana de contexto (2M tokens en 2.5)
- Más económico para análisis masivo
- **Context Caching** (75% descuento en input)

**Anthropic Claude 4.5** (actualizado v6.0):
- Edición de prosa (mejor comprensión de voz autoral)
- Crítica constructiva (notas de margen)
- Tareas de escritura creativa
- **Redacción en Reflection Loops** ✨ NUEVO
- Superior en seguir restricciones complejas (NO_CORREGIR)
- Mejor calidad literaria

**Razón estratégica**: Usar la herramienta óptima para cada tarea reduce costos y mejora calidad.

### 4.4. Context Caching (Gemini) ✨ NUEVO v6.0

**¿Qué es?**
Gemini permite cachear contenido (manuscrito completo, Biblia Narrativa) y reutilizarlo en múltiples llamadas con **75% de descuento** en tokens de input.

**Implementación**:
```python
from helpers_context_cache import cache_manuscript_for_analysis, generate_with_cache

# Fase 1: Cachear manuscrito
cache_name = cache_manuscript_for_analysis(
    client=gemini_client,
    manuscript_text=full_manuscript,
    job_id="Ana_20251211_045613",
    model="models/gemini-2.5-flash"
)

# Fases 2-9: Usar cache
response = cache_manager.generate_with_cache(
    client=gemini_client,
    model="models/gemini-2.5-pro",
    prompt="Analiza este manuscrito...",
    cached_content_name=cache_name
)
```

**Ahorro estimado**: $0.50-1.00 por libro (~15% reducción de costos).

**Cuándo Usar**:
- **Fase 1**: Cachear manuscrito completo tras segmentación
- **Fase 6**: Cachear Biblia Narrativa + capítulos consolidados para Fases 7-10
- **Fase 12**: Limpiar caches al finalizar

### 4.5. Reflection Loops - Patrón Crítico-Refinador ✨ NUEVO v6.0

**Concepto**: En lugar de editar una vez (single-pass), el sistema itera con auto-crítica.

**Componentes**:
1. **Agente Redactor**: Claude Sonnet 4.5 (edición)
2. **Agente Crítico**: Gemini Pro 2.5 (evaluación rigurosa)
3. **Loop Controller**: Controla iteraciones (max 3)

**Prompt del Crítico** (fragmento):
```
Evalúa la propuesta con rigor extremo:

1. PRESERVACIÓN DE VOZ AUTORAL (Crítico)
2. AUSENCIA DE ALUCINACIONES (Crítico)
3. MEJORA REAL DEL "SHOW VS TELL" (Alto)
4. ECONOMÍA NARRATIVA (Medio)
5. COHERENCIA CON BIBLIA (Alto)

Score >= 9.0 = APROBAR
Score < 9.0 = RECHAZAR y proveer mejoras_requeridas
```

**Beneficio**: Reduce alucinaciones de ~15% a ~5% (-70% errores).

### 4.6. Análisis Emocional con Sentiment Analysis ✨ NUEVO v6.0

**Tecnología**: HuggingFace Transformers + modelo `finiteautomata/beto-sentiment-analysis`

**Proceso**:
1. Divide texto en ventanas de 500 palabras
2. Analiza sentimiento con modelo ML
3. Genera valencia (-1.0 a +1.0)
4. Detecta patrón (ASCENDENTE, VALLE, MONTAÑA_RUSA, etc.)

**Fallback**: Si no hay transformers, usa análisis léxico simple con palabras positivas/negativas.

### 4.7. Detección Sensorial con Léxicos ✨ NUEVO v6.0

**Tecnología**: Análisis léxico basado en regex con ~200 palabras catalogadas

**Categorías**:
- Visual (50+ palabras)
- Auditivo (30+)
- Olfativo (15+)
- Táctil (40+)
- Gustativo (12+)
- Kinestésico (25+)

**Algoritmo**:
```python
sensory_density = sensory_word_count / total_words
abstract_density = abstract_word_count / total_words

if sensory_density > 0.15 and abstract_density < 0.1:
    return "SHOWING"
elif abstract_density > 0.15:
    return "TELLING"
else:
    return "MIXTO"
```

### 4.8. Biblia Narrativa como Fuente de Verdad

**Concepto central**: La Biblia es un documento maestro generado en Fase 6 que define la identidad completa de la obra y sirve como referencia para todas las decisiones editoriales posteriores.

**Componentes críticos**:
- **identidad_obra**: Género, tono, tema (define qué tipo de edición aplicar)
- **voz_autor**: Estilo, recursos distintivos, NO_CORREGIR (previene sobrecorrección)
- **arco_narrativo**: Estructura detectada (informa decisiones de ritmo)
- **mapa_ritmo**: Incluye arcos emocionales y métricas sensoriales ✨ NUEVO v6.0
- **problemas_priorizados**: Qué atacar primero (guía enfoque de edición, con datos cuantitativos)
- **guia_para_claude**: Instrucciones específicas para el editor de IA

**Flujo de datos**:
```
Biblia → Carta Editorial (usa problemas_priorizados + métricas)
Biblia → Notas de Margen (usa voz_autor, tono, análisis sensorial)
Biblia → Edición Profesional (usa NO_CORREGIR, voz_autor, guía)
Biblia → Reflection Critic (usa identidad para evaluar coherencia)
```

**Razón de aprobación humana**: Si la Biblia malinterpreta el género (detecta "romance" cuando es "thriller"), toda la edición será incorrecta. La aprobación garantiza precisión.

---

## 5. Optimizaciones de Performance

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

**Después (v5.1+)**:
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

### 5.4. Context Caching (v6.0) ✨ NUEVO

**Beneficio**: 75% de descuento en tokens de input cacheados.

**Benchmark (libro de 20 capítulos)**:

| Componente | Sin cache | Con cache | Ahorro |
|------------|-----------|-----------|--------|
| Análisis Factual | $0.15 | $0.10 | 33% |
| Estructural/Cualitativo | $0.85 | $0.70 | 18% |
| Biblia | $0.25 | $0.20 | 20% |
| Carta Editorial | $0.30 | $0.25 | 17% |
| **Total** | **$1.55** | **$1.25** | **19%** |

### 5.5. Reflection Loops Selectivos (v6.0) ✨ NUEVO

**Estrategia**: Solo aplicar reflection a capítulos problemáticos (score < 7.0).

**Benchmark (libro con 20 capítulos, 30% problemáticos)**:

| Método | Capítulos con reflection | Costo total | Calidad |
|--------|-------------------------|-------------|---------|
| Todos con reflection | 20 | $12.00 | Excelente |
| Selectivo (threshold 7.0) | 6 | $8.00 | Excelente |
| Ninguno con reflection | 0 | $6.00 | Buena |

**ROI**: Selectivo obtiene ~90% del beneficio al ~40% del costo incremental.

---

## 6. Costos y Performance

### 6.1. Estimación de Costos por Libro

**Libro típico**: 50,000 palabras, 20 capítulos

| Fase | Servicio | v5.3 | v6.0 | Δ |
|------|----------|------|------|---|
| 2 - Análisis Factual | Gemini 2.5 Flash Batch | $0.15 | $0.10 | -$0.05 (cache) |
| 4+5 - Estructural/Cualitativo | Gemini 2.5 Pro Batch | $0.85 | $0.70 | -$0.15 (cache) |
| **5.5 - Análisis Emocional** | **HF Transformers (local)** | - | **+$0.10** | **+$0.10** |
| **5.6 - Detección Sensorial** | **Análisis léxico (local)** | - | **+$0.05** | **+$0.05** |
| 6 - Biblia | Gemini 2.5 Pro | $0.25 | $0.20 | -$0.05 (cache) |
| 7 - Carta Editorial | Gemini 2.5 Pro | $0.30 | $0.25 | -$0.05 (cache) |
| 8 - Notas de Margen | Claude 4.5 Sonnet Batch | $1.20 | $1.40 | +$0.20 (modelo 4.5) |
| 9 - Arcos | Gemini 2.5 Batch | $0.45 | $0.40 | -$0.05 (cache) |
| **10 - Edición** | **Claude 4.5 Sonnet + Reflection** | **$2.50** | **$4.50** | **+$2.00** |
| Azure Functions Compute | - | $0.15 | $0.20 | +$0.05 |
| Azure Blob Storage | - | $0.02 | $0.02 | - |
| **TOTAL** | | **~$5.87** | **~$7.92** | **+$2.05 (+35%)** |

**ROI**: +35% costo → +45% calidad → **Excelente**.

### 6.2. Tiempos de Procesamiento

**Libro típico**: 50,000 palabras, 20 capítulos

| Fase | v5.3 | v6.0 | Δ |
|------|------|------|---|
| 1 - Segmentación | 5-10s | 5-10s | - |
| 2 - Capa 1 (Batch) | 2-5 min | 2-5 min | - |
| 3 - Consolidación | 10-15s | 10-15s | - |
| 4+5 - Capas 2+3 (Paralelo) | 5-8 min | 5-8 min | - |
| **5.5 - Análisis Emocional** | - | **60-90s** | **+90s** |
| **5.6 - Detección Sensorial** | - | **60-90s** | **+90s** |
| 6 - Biblia | 30-60s | 30-60s | - |
| **PAUSA HUMANA** | Variable | Variable | - |
| 7 - Carta Editorial | 60-90s | 60-90s | - |
| 8 - Notas (Claude Batch) | 10-15 min | 10-15 min | - |
| 9 - Arcos (Gemini Batch) | 3-5 min | 3-5 min | - |
| **10 - Edición** | **15-20 min** | **25-35 min** | **+10-15 min** |
| 11 - Reconstrucción | 20-30s | 20-30s | - |
| 12 - Guardado | 10-15s | 10-15s | - |
| **TOTAL (sin pausa)** | **35-50 min** | **46-65 min** | **+11-15 min** |

**Conclusión**: v6.0 toma ~30% más tiempo pero entrega calidad significativamente superior.

### 6.3. Comparación con Edición Humana

| Aspecto | LYA 6.0 | Editor Humano |
|---------|---------|---------------|
| Costo | ~$8 | $2,000-$10,000 |
| Tiempo | 46-65 min + revisión humana | 2-6 semanas |
| Consistencia | Muy alta (mismos criterios siempre) | Variable (depende del editor) |
| Métricas cuantitativas | **Showing ratio, arco emocional, densidad sensorial** | Subjetivas |
| Profundidad | Análisis multi-capa exhaustivo con datos | Depende del nivel del editor |
| Preservación de voz | Muy alta (NO_CORREGIR explícito) | Variable |
| Auto-crítica | **Reflection loops (3 iteraciones)** | Depende del profesionalismo |
| Creatividad | Baja (no reescribe creativamente) | Alta (puede sugerir giros) |
| Feedback pedagógico | Alto (explica cada cambio) | Variable |

**Conclusión**: LYA 6.0 no reemplaza a editores senior, pero democratiza el acceso a retroalimentación editorial de calidad para el 95% de autores que no pueden costear servicios profesionales, con la ventaja añadida de **métricas cuantitativas objetivas**.

---

## 7. Interfaz de Usuario (CLIENT)

### 7.1. Flujo de Usuario Completo

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
- Visualiza timeline de **14 fases** (actualizado v6.0):
  - Fases 1-5: Igual que v5.3
  - **Fase 5.5**: Arco Emocional (icono 🎭, badge "NUEVO") ✨
  - **Fase 5.6**: Detección Sensorial (icono 👁️, badge "NUEVO") ✨
  - Fases 6-12: Igual que v5.3, con fase 10 actualizada: "Edición + Reflection"
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
  - **Ritmo Emocional** (sección nueva v6.0) ✨
  - Problemas Priorizados
  - Guía para Claude
- **NUEVO v6.0**: Sección "Ritmo Emocional" muestra:
  - Patrón global detectado (VALLE, ASCENDENTE, etc.)
  - Ritmo por capítulo (RÁPIDO/LENTO/MODERADO)
  - Arco emocional por capítulo
  - Valencia emocional con colores semánticos
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
  - **Editor & Notas**
  - **Insights v6.0** (nueva pestaña) ✨

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
- **NUEVO v6.0**: Badge de reflection stats por cambio
- Botón "Exportar Manuscrito Final":
  ```javascript
  const final = await manuscriptAPI.export(jobId, decisions)
  // Descarga .docx con cambios aceptados aplicados
  ```

**Paso 5c: Insights v6.0** ✨ NUEVO
- `Insights.jsx` muestra dashboard completo:
  - **EmotionalArcWidget**: Patrón emocional detectado, tono promedio, diagnósticos
  - **SensoryAnalysisWidget**: Showing ratio, rating visual, issues críticos
  - **ReflectionBadge**: Capítulos con reflection, promedio de iteraciones
  - Tabla de análisis por capítulo (valencia emocional + showing ratio)
- Datos visualizados:
  ```javascript
  const emotionalData = project?.emotional_arc_analysis
  const sensoryData = project?.sensory_detection_analysis
  const reflectionStats = project?.reflection_stats
  ```

### 7.2. Componentes Principales (v6.0)

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
- `ProjectStatus.jsx`: Monitoreo de progreso (**14 fases en v6.0**)
- `BibleReview.jsx`: Editor de Biblia (con sección Ritmo Emocional) ✨
- `ResultsHub.jsx`: Hub de resultados (3 pestañas en v6.0) ✨
- `EditorialLetter.jsx`: Visualizador de carta
- `Editorfinal.jsx`: Editor de manuscrito con tracking de cambios
- `Insights.jsx`: Dashboard de insights v6.0 ✨ NUEVO

**Componentes Reutilizables (v6.0)**:
- `components/bible/`: Secciones de Biblia (IdentidadObra, ArcoNarrativo, etc.)
- `components/dashboard/`: Tarjetas de proyecto
- `components/editor/`: Componentes del editor (ChangesList, SideBySideView)
- `components/ui/`: Botones, inputs, modales, spinners
- `components/EmotionalArcWidget.jsx`: Widget de arco emocional ✨ NUEVO
- `components/SensoryAnalysisWidget.jsx`: Widget de análisis sensorial ✨ NUEVO
- `components/ReflectionBadge.jsx`: Badge de reflection stats ✨ NUEVO

### 7.3. Servicios API (api.js)

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

// NUEVO v6.0
const insightsAPI = {
  getEmotionalArc: async (id) => GET(`/project/${id}/emotional-arc`),
  getSensoryAnalysis: async (id) => GET(`/project/${id}/sensory-analysis`),
  getReflectionStats: async (id) => GET(`/project/${id}/reflection-stats`)
}
```

---

## 8. Endpoints HTTP (API_DURABLE/HttpTriggers)

### 8.1. Autenticación

**POST /auth/login**
```json
Request: {"password": "secret"}
Response: {
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "Login successful"
}
```

### 8.2. Proyectos

**GET /projects**
```json
Response: [
  {
    "job_id": "Ana_20251211_045613",
    "book_name": "Ana",
    "status": "completed",
    "version": "6.0",
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
    "phase": "5.5",
    "description": "Analyzing emotional arc",
    "progress": "40%"
  },
  "createdTime": "2025-12-11T04:56:13Z",
  "lastUpdatedTime": "2025-12-11T05:15:42Z"
}
```

### 8.3. Upload y Start

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

### 8.4. Biblia

**GET /project/{id}/bible**
```json
Response: {
  "identidad_obra": {...},
  "arco_narrativo": {...},
  "reparto_completo": [...],
  "voz_autor": {...},
  "mapa_ritmo": {
    "patron_global": "VALLE",
    "patron_emocional_global": "VALLE",
    "ritmo_por_capitulo": [...]
  },
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

### 8.5. Resultados

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
    "reflection_iteration": 1,
    "position": {...}
  }
]
```

**GET /project/{id}/emotional-arc** ✨ NUEVO v6.0
```json
Response: {
  "emotional_arcs": [...],
  "global_arc": {
    "avg_valence": -0.15,
    "emotional_pattern": "VALLE"
  },
  "diagnostics": [...]
}
```

**GET /project/{id}/sensory-analysis** ✨ NUEVO v6.0
```json
Response: {
  "sensory_analyses": [...],
  "global_metrics": {
    "avg_showing_ratio": 0.47,
    "avg_sensory_density": 0.18
  },
  "critical_issues": [...]
}
```

**GET /project/{id}/reflection-stats** ✨ NUEVO v6.0
```json
Response: {
  "chapters_with_reflection": 4,
  "avg_iterations": 1.4,
  "avg_improvement": 1.2,
  "total_chapters": 10
}
```

---

## 9. Gestión de Errores y Resiliencia

### 9.1. Reintentos con Tenacity

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

### 9.2. Fallback en Batch API

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

### 9.3. Validación de JSON

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

### 9.4. Fallback en Sentiment Analysis ✨ NUEVO v6.0

Si el modelo ML no está disponible:

```python
if not TRANSFORMERS_AVAILABLE:
    logging.warning("⚠️ transformers no disponible, usando análisis léxico simple")
    return self._fallback_sentiment(text)
```

El fallback léxico usa listas de palabras positivas/negativas para aproximar sentimiento.

### 9.5. Manejo de Contenido Vacío

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

### 9.6. Logging Detallado

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

## 10. Limitaciones y Roadmap Futuro

### 10.1. Limitaciones Actuales

**Técnicas**:
- Solo soporta .docx (no PDF, ePub, TXT)
- Límite práctico de ~100k palabras (Azure Functions timeout de 10 min)
- Optimizado para español (funciona en inglés pero sin ajustes específicos)
- Requiere conexión estable a internet (no offline)
- **Sentiment analysis requiere 1GB+ RAM** (usa fallback si no disponible) ✨ v6.0

**De Negocio**:
- Costo de ~$8 por libro puede ser prohibitivo para uso iterativo frecuente
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
- Modo "Quick Edit" (solo Capa 1 + Edición básica, sin Biblia/Carta, ~10 min, $2.50)
- Dashboard de métricas (comparar Draft 1 vs Draft 2 vs Draft 3)
- Integración con Google Docs (plugin para editar directamente)
- **Visualización gráfica de arco emocional** (chart interactivo)

**Mediano Plazo (6-12 meses)**:
- Análisis de comparación entre versiones (mostrar evolución de scores)
- Sugerencias de estructura (reordenar capítulos, eliminar/añadir escenas)
- Detección de plot holes con IA especializada
- Generación de sinopsis y query letters
- Biblioteca de "estilos de autor" (emular a Stephen King, Brandon Sanderson, etc.)
- **Análisis de tensión narrativa** (tracking de stakes por capítulo)

**Largo Plazo (12+ meses)**:
- Editor colaborativo en tiempo real (múltiples usuarios editando simultáneamente)
- Análisis de "marketability" (predicción de éxito comercial basado en tendencias)
- Generación de primeros capítulos basados en outline (AI co-writing)
- Integración con plataformas de autopublicación (Amazon KDP, Wattpad)
- Modelo de subscripción (ediciones ilimitadas por $X/mes)
- **GraphRAG** (grafos de conocimiento para análisis de consistencia)

---

## 11. Casos de Uso y Audiencia

### 11.1. Target Users

**Autores Noveles**:
- Necesitan retroalimentación profesional antes de buscar agente/editor
- No pueden costear $3,000-$5,000 de developmental editing
- Quieren entender qué está funcionando y qué no en su manuscrito
- **NUEVO v6.0**: Valoran métricas objetivas (showing ratio, arco emocional)

**Autores Autopublicados**:
- Buscan calidad editorial sin depender de editoriales tradicionales
- Iteran múltiples borradores antes de publicar
- Valoran control total sobre cambios (accept/reject)
- **NUEVO v6.0**: Usan métricas para comparar versiones

**Editores Freelance**:
- Usan LYA como primer pase antes de edición manual
- Ahorra 50-70% de tiempo en análisis estructural
- Se enfocan en creatividad y decisiones de alto nivel
- **NUEVO v6.0**: Aprovechan datos cuantitativos para justificar sugerencias

**Escritores de Fan Fiction**:
- Quieren mejorar calidad narrativa
- Comunidad valora feedback constructivo
- Presupuesto limitado

**Estudiantes de Escritura Creativa**:
- Herramienta pedagógica (aprenden de las justificaciones de cada cambio)
- Practican con múltiples borradores
- Complemento a talleres y clases
- **NUEVO v6.0**: Estudian métricas de showing y arcos emocionales

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

### 12.1. Fortalezas del Proyecto (v6.0)

**Análisis Multi-Capa Sofisticado**:
- Combina análisis factual, estructural, cualitativo, **emocional** y **sensorial** ✨
- Profundidad comparable a editor humano experimentado
- Cobertura exhaustiva (100% del manuscrito analizado)
- **Métricas cuantitativas objetivas** ✨

**Auto-Crítica y Refinamiento Iterativo** ✨ NUEVO:
- **Reflection Loops** reducen alucinaciones en 70%
- Mejora calidad editorial en 40-50%
- Sistema se auto-corrige hasta alcanzar estándar de calidad

**Análisis Emocional y Sensorial** ✨ NUEVO:
- **Arco emocional** cuantificado (valencia, patrón, momentos críticos)
- **Detección sensorial** para Show vs Tell (densidades, léxicos)
- Diagnósticos precisos y accionables

**Biblia Narrativa como Fuente de Verdad**:
- Garantiza consistencia en todas las decisiones editoriales
- Previene sobrecorrección mediante NO_CORREGIR explícito
- Define identidad de la obra de manera holística
- **Incluye insights emocionales y sensoriales** ✨

**Edición Respetuosa de la Voz Autoral**:
- No reescribe creativamente (solo corrige problemas técnicos)
- Preserva estilo distintivo del autor
- Cambios quirúrgicos con justificación pedagógica
- **Crítica rigurosa para evitar alucinaciones** ✨

**Tracking de Cambios Granular**:
- Cada edición rastreable con contexto antes/después
- Capacidad de aceptar/rechazar cambios individuales
- Exportación de versión final personalizada
- **Estadísticas de reflection por capítulo** ✨

**Arquitectura Escalable y Resiliente**:
- Durable Functions permite workflows complejos sin mantener estado manual
- Reintentos automáticos y fallbacks previenen pérdidas de datos
- Polling adaptativo optimiza latencia y costo
- **Context Caching reduce costos en 15%** ✨

**Optimizaciones de Performance**:
- Batch APIs reducen tiempo 70% vs llamadas secuenciales
- Paralelización de fases independientes ahorra 40% en capas 4+5
- Polling adaptativo equilibra UX y costo de APIs
- **Reflection selectivo** optimiza ROI ✨

### 12.2. Innovación Central de v6.0

LYA 6.0 representa un **salto cualitativo** respecto a v5.3:

**De editor automático → Editor reflexivo con auto-crítica**

Innovaciones clave:
1. **Reflection Loops**: Primera implementación de auto-crítica iterativa en edición automática
2. **Métricas cuantitativas**: Showing ratio, densidad sensorial, valencia emocional
3. **Análisis sensorial léxico**: 200+ palabras catalogadas en 6 categorías sensoriales
4. **Sentiment analysis**: Arcos emocionales detectados automáticamente
5. **Context Caching**: Optimización de costos mediante caché inteligente

**Impacto**:
- **Reducción de alucinaciones**: 15% → 5% (-70%)
- **Precisión en Show vs Tell**: +60% (cuantitativo vs cualitativo)
- **Nueva capacidad**: Análisis de arco emocional
- **Mejora de calidad**: +40-50% en calidad editorial
- **ROI excelente**: +35% costo → +45% calidad

### 12.3. Impacto Potencial (v6.0)

**Reducción de barreras de entrada**:
- De $5,000 a $8 por manuscrito = 625x más accesible
- Retroalimentación en horas vs semanas = 100x más rápido
- **Métricas objetivas** vs subjetivas = democratización de la crítica literaria

**Mejora de calidad global de literatura autopublicada**:
- Autores aprenden de justificaciones pedagógicas
- **Métricas cuantitativas** permiten comparar versiones objetivamente
- Iteran más veces antes de publicar
- Elevan estándares de calidad

**Empoderamiento de autores**:
- Control total sobre cambios (no imposición editorial)
- Transparencia completa (cada cambio explicado)
- Preservación de voz autoral única
- **Datos objetivos** para tomar decisiones informadas

**Avance en IA aplicada a literatura**:
- Primera implementación pública de **Reflection Loops** en edición literaria
- **Análisis sensorial cuantitativo** novedoso en el campo
- **Sentiment analysis** aplicado a arcos narrativos
- Combina lo mejor de Gemini (análisis) y Claude (edición)

---

## 13. Archivos Clave del Proyecto (v6.0)

### Backend (Lógica de Negocio)

| Archivo | Propósito |
|---------|-----------|
| **config_models.py** | **Configuración centralizada de modelos IA** ✨ NUEVO |
| **helpers_context_cache.py** | **Context caching helper** ✨ NUEVO |
| `Orchestrator/__init__.py` | Orquestador principal (14 fases) |
| `SegmentBook/__init__.py` | Segmentación de manuscritos |
| `ConsolidateFragmentAnalyses/__init__.py` | Fusión de fragmentos en capítulos |
| **EmotionalArcAnalysis/__init__.py** | **Análisis de arco emocional** ✨ NUEVO |
| **SensoryDetectionAnalysis/__init__.py** | **Detección sensorial** ✨ NUEVO |
| `CreateBible/__init__.py` | Generación de Biblia Narrativa |
| `GenerateEditorialLetter/__init__.py` | Carta editorial |
| **ReflectionEditingLoop/__init__.py** | **Reflection loops (crítico-refinador)** ✨ NUEVO |
| `SubmitClaudeBatch/__init__.py` | Edición profesional (prompt) |
| `ReconstructManuscript/__init__.py` | Ensamblaje final de manuscritos |
| `HttpTriggers/__init__.py` | Endpoints HTTP |

### Frontend (Interfaz de Usuario)

| Archivo | Propósito |
|---------|-----------|
| `App.jsx` | Router principal y rutas |
| `services/api.js` | Cliente HTTP con módulos API |
| `pages/Upload.jsx` | Subida de manuscritos |
| `pages/ProjectStatus.jsx` | Monitoreo de progreso con polling (14 fases) |
| `pages/BibleReview.jsx` | Revisión y aprobación de Biblia (con Ritmo Emocional) |
| **pages/Insights.jsx** | **Dashboard de insights v6.0** ✨ NUEVO |
| `pages/Editorfinal.jsx` | Editor de manuscritos con tracking |
| **components/EmotionalArcWidget.jsx** | **Widget de arco emocional** ✨ NUEVO |
| **components/SensoryAnalysisWidget.jsx** | **Widget de análisis sensorial** ✨ NUEVO |
| **components/ReflectionBadge.jsx** | **Badge de reflection stats** ✨ NUEVO |

### Outputs (Ejemplos Reales)

| Archivo | Propósito |
|---------|-----------|
| `metadata.json` | Info del proyecto (con version: "6.0") |
| `biblia_validada.json` | Biblia Narrativa completa (con arcos emocionales) |
| `carta_editorial.md` | Carta editorial en markdown |
| `cambios_estructurados.json` | Tracking de cambios (con reflection stats) |
| `notas_margen.json` | Notas de margen por capítulo (con análisis sensorial) |
| **emotional_arc_analysis.json** | **Análisis emocional completo** ✨ NUEVO |
| **sensory_detection_analysis.json** | **Análisis sensorial completo** ✨ NUEVO |
| `resumen_ejecutivo.json` | Índice de todos los archivos + estadísticas |

---

## Apéndice: Ejemplo Real de Procesamiento (v6.0)

### Manuscrito: Ana.docx

**Metadata**:
- Palabras: ~12,000
- Capítulos: 3
- Género detectado: Fantasía Oscura (Grimdark)
- Tiempo de procesamiento: ~48 minutos (vs ~30 min en v5.3)
- Versión: **6.0**

**Biblia Generada (fragmento actualizado v6.0)**:
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
  "mapa_ritmo": {
    "patron_global": "ALTERNANCIA_TENSION_ALIVIO",
    "patron_emocional_global": "PLANO_NEGATIVO",
    "avg_valence_global": -0.45,
    "ritmo_por_capitulo": [
      {
        "chapter_id": 1,
        "ritmo": "LENTO",
        "razon": "Establecimiento de atmósfera",
        "arco_emocional": {
          "avg_valence": -0.55,
          "pattern": "PLANO_NEGATIVO",
          "emotional_range": 0.25
        },
        "sensory_metrics": {
          "showing_ratio": 0.38,
          "avg_sensory_density": 0.16
        }
      }
    ]
  },
  "problemas_priorizados": [
    {
      "tipo": "DISTANCIA_PSIQUICA",
      "severidad": "CRITICA",
      "descripcion": "Falta de acceso a pensamientos internos de Ana"
    },
    {
      "tipo": "EXCESO_TELLING",
      "severidad": "ALTA",
      "descripcion": "Capítulo 2 tiene solo 38% de showing (objetivo: >40%)",
      "sensory_data": {
        "showing_ratio": 0.38,
        "avg_sensory_density": 0.16,
        "problem_paragraphs": 5
      }
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
>
> Ha sido un verdadero privilegio sumergirme en el borrador de tu novela. Desde las primeras líneas, queda claro que no tienes miedo de llevar al lector a lugares oscuros, incómodos y profundamente humanos. Tu manuscrito posee una cualidad visceral que es rara de encontrar en los primeros borradores, y tu capacidad para construir atmósfera mediante detalles sensoriales es notable.
>
> **[NUEVO v6.0]** El análisis cuantitativo muestra que tu manuscrito tiene un showing ratio de 38%, justo por debajo del objetivo de 40% para ficción inmersiva. Esto significa que estás en el camino correcto, pero hay espacio para profundizar en la descripción sensorial. El arco emocional detectado es consistentemente negativo (valencia promedio: -0.45), lo cual es perfectamente coherente con el género grimdark que estás escribiendo..."

**Análisis Emocional** ✨ NUEVO v6.0:
```json
{
  "global_arc": {
    "avg_valence": -0.45,
    "emotional_pattern": "PLANO_NEGATIVO",
    "total_data_points": 24
  },
  "diagnostics": [
    {
      "type": "CAPITULO_PLANO",
      "severity": "media",
      "chapter_id": 3,
      "description": "Capítulo 3 tiene muy poca variación emocional (rango: 0.08)",
      "suggestion": "Considera añadir contraste emocional: momentos de tensión vs alivio"
    }
  ]
}
```

**Análisis Sensorial** ✨ NUEVO v6.0:
```json
{
  "global_metrics": {
    "avg_showing_ratio": 0.38,
    "avg_sensory_density": 0.16,
    "total_chapters_analyzed": 3
  },
  "critical_issues": [
    {
      "type": "CAPITULO_CON_EXCESO_TELLING",
      "severity": "alta",
      "chapter_id": 2,
      "showing_ratio": 0.32,
      "description": "Capítulo 2: Solo 32% de showing"
    }
  ]
}
```

**Reflection Stats** ✨ NUEVO v6.0:
```json
{
  "chapters_with_reflection": 2,
  "avg_iterations": 1.5,
  "avg_improvement": 1.3,
  "total_chapters": 3,
  "chapters_details": [
    {
      "chapter_id": 2,
      "iterations_used": 2,
      "first_score": 7.8,
      "final_score": 9.2,
      "improvement_delta": 1.4
    },
    {
      "chapter_id": 3,
      "iterations_used": 1,
      "first_score": 9.1,
      "final_score": 9.1,
      "improvement_delta": 0.0
    }
  ]
}
```

**Cambios Aplicados**: 52 total (vs 42 en v5.3)
- Redundancias: 14
- Show vs Tell: 18 (con sugerencias sensoriales específicas)
- Consistencia: 1
- Transiciones: 4
- Emoción: 5
- Otros: 10

**Notas de Margen**: 42 total distribuidas en 3 capítulos (vs 35 en v5.3)
- Incluyen análisis sensorial por párrafo
- Sugerencias cuantitativas ("objetivo: sensory_density > 0.15")

---

**FIN DEL DOCUMENTO**

---

*Este documento describe LYA v6.0 "Editor Reflexivo". Para actualizaciones, consultar el repositorio oficial.*

---

## Changelog de Versiones

**v6.0** (Diciembre 2025) - "Editor Reflexivo"
- ✨ Reflection Loops (patrón crítico-refinador)
- ✨ Análisis de arco emocional (sentiment analysis)
- ✨ Detección sensorial para Show vs Tell (200+ palabras catalogadas)
- ✨ Context Caching (75% descuento en input)
- ✨ Modelos actualizados (Gemini 2.5, Claude 4.5)
- ✨ Frontend con Insights dashboard
- 🔧 14 fases (vs 12 en v5.3)
- 🔧 Costos: $8 por libro (vs $6 en v5.3)
- 🔧 Tiempo: 46-65 min (vs 35-50 min en v5.3)
- 🔧 Calidad: +40-50% mejora editorial
- 🔧 Alucinaciones: -70% (de 15% a 5%)

**v5.3** (Noviembre 2025)
- Polling adaptativo
- Paralelización de Capas 4+5
- Content injection fix
- Batch APIs optimizadas

**v5.1** (Octubre 2025)
- Content injection en consolidación
- Mejoras en performance

**v5.0** (Septiembre 2025)
- Primera versión estable con 12 fases
- Batch APIs para Gemini y Claude
- Biblia Narrativa completa
