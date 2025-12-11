# 📝 Regenerar Carta Editorial

Este documento explica cómo regenerar **solo la Carta Editorial** sin tener que reprocesar todo el manuscrito.

## ¿Cuándo usar esto?

- ✅ Ya tienes una Biblia Narrativa generada
- ✅ La Carta Editorial falló o está vacía
- ✅ Quieres regenerar la carta con cambios en el prompt
- ✅ Estás debuggeando el proceso

## 🚀 Opción 1: Script Python (Recomendado)

### Requisitos
```bash
pip install requests
```

### Uso
```bash
# Asegúrate de que Azure Functions esté corriendo
func start

# En otra terminal, ejecuta:
python regenerate_carta.py 2110_20251210_223051
```

## 🔧 Opción 2: cURL directo

```bash
curl -X POST http://localhost:7071/api/project/2110_20251210_223051/editorial-letter/regenerate
```

## 📊 Qué hace este endpoint

1. **Carga datos existentes** del blob storage:
   - `biblia_validada.json`
   - `capitulos_consolidados.json`
   - `metadata.json`

2. **Ejecuta GenerateEditorialLetter** directamente
   - Usa Gemini 2.5 Pro
   - Genera carta completa con todas las secciones

3. **Guarda resultados** en blob storage:
   - `carta_editorial.json`
   - `carta_editorial.md`
   - Actualiza `metadata.json` a status: `completed`

## ⏱️ Tiempo estimado

- **~60-120 segundos** (depende de la respuesta de Gemini API)

## 📋 Logs

Revisa los logs del Azure Function para ver el progreso:

```bash
# En la terminal donde corriste func start verás:
✅ Biblia cargada
✅ Capítulos consolidados cargados (8 caps)
✅ Metadata cargada: Sin título
✅ Módulo GenerateEditorialLetter cargado
🔄 Llamando a GenerateEditorialLetter...
📝 Generando Carta Editorial para: Sin título
✅ Modelo Gemini inicializado
🔄 Llamando a Gemini API...
✅ Respuesta recibida de Gemini
✅ JSON parseado exitosamente
✅ Carta Editorial generada exitosamente
✅ carta_editorial.json guardada
✅ carta_editorial.md guardada
✅ Metadata actualizada a 'completed'
```

## 🐛 Troubleshooting

### Error: "No se encontró la biblia"
- Verifica que el job_id sea correcto
- Asegúrate de que la biblia fue generada previamente

### Error: "No se pudo conectar al servidor"
- Inicia Azure Functions: `func start`
- Verifica que esté corriendo en `localhost:7071`

### Error: "Respuesta de Gemini vacía"
- Revisa tu `GEMINI_API_KEY` en `local.settings.json`
- Verifica que tengas créditos en Google AI Studio
- Revisa los logs completos para ver el error de Gemini

### La carta se genera pero está vacía
- Revisa los logs para ver si Gemini retornó JSON válido
- Puede ser un problema con el prompt o el modelo

## 🔍 Verificar resultados

Después de regenerar, puedes:

1. **Descargar desde blob storage:**
   - Usa Azure Storage Explorer
   - O descarga directamente desde el portal

2. **Ver en el frontend:**
   - Navega a `/proyecto/2110_20251210_223051/resultados`
   - Ahora debería aparecer la Carta Editorial

3. **Usar el endpoint GET:**
   ```bash
   curl http://localhost:7071/api/project/2110_20251210_223051/editorial-letter
   ```

## 💡 Tip

Si quieres regenerar TAMBIÉN las notas de margen, tendrás que ejecutar el proceso completo o crear un endpoint similar para ellas.
