# CODEBASE MEMORY & CONTEXT RULES
# Propósito: Protocolo de uso de codebase-memory-mcp como mapa del sistema.
# El MCP reduce el descubrimiento — no sustituye la verificación del código.
# OPCIONAL: activar solo si el proyecto usa un MCP de memoria (AGENTS.md §J).
# Sin MCP disponible → búsqueda local dirigida (AGENTS.md §B).

## 1. FUENTES DE VERDAD Y PRECEDENCIA

```
Spec aprobada      → comportamiento esperado
Código actual      → implementación real
Tests / ADRs       → comportamiento verificado y decisiones arquitectónicas
Codebase Memory    → mapa derivado para descubrimiento e impacto
```

- Memory no sustituye la inspección del código cuando se necesita precisión.
- Si Memory contradice código o spec → verificar la fuente superior y actualizar Memory si está obsoleto.
- **Prohibido** registrar propuestas o intenciones como funcionalidad implementada.

## 2. FLUJO DE DESCUBRIMIENTO

Antes de crear o modificar elementos:

```
1. search_graph / query_graph en Memory
2. Buscar conceptos equivalentes (no solo coincidencias exactas)
3. Localizar implementaciones relacionadas
4. Inspeccionar únicamente el código fuente relevante
5. Implementar
```

No concluir que algo no existe porque la primera búsqueda no devolvió resultados.

Antes de crear componentes, servicios, repositorios, validators, helpers, modelos o API clients → comprobar que no exista una implementación reutilizable.

## 3. ANÁLISIS DE IMPACTO

Antes de modificar elementos compartidos o estructurales, identificar consumidores mediante `trace_path` o equivalente.

Obligatorio para cambios en:
- componentes compartidos
- modelos/relaciones de base de datos
- entidades de dominio
- contratos y endpoints API
- servicios/repositorios públicos
- autenticación/autorización
- configuración transversal

No eliminar código basándose únicamente en ausencia de imports directos. Comprobar routing, DI, configuración dinámica y consumidores indirectos.

## 4. QUÉ REGISTRAR EN MEMORY

**Registrar** — conocimiento estructural reutilizable:
- arquitectura y módulos
- componentes compartidos y su responsabilidad
- entidades, relaciones y servicios públicos
- endpoints y contratos relevantes
- dependencias entre features
- patrones transversales
- elementos deprecados y sus reemplazos

**No registrar:**
- cuerpos completos de código
- variables locales o helpers triviales
- detalles de debugging o logs
- cambios puramente visuales/locales
- información sin valor arquitectónico

Memory es un **mapa** del sistema, no una copia del repositorio.

## 5. CUÁNDO SINCRONIZAR MEMORY

Actualizar Memory después de:
- crear/modificar/eliminar componentes compartidos
- crear/modificar/eliminar endpoints o contratos
- cambios en entidades, relaciones o esquemas
- cambios arquitectónicos
- mover, renombrar o deprecar elementos relevantes
- cambios importantes en ownership, seguridad o multi-tenancy

No actualizar Memory por cambios triviales o locales.
Registrar solo después de que la implementación esté creada y validada.
Preferir actualización incremental sobre rebuild completo.

## 6. AHORRO DE CONTEXTO

Orden de preferencia para descubrimiento:
```
Memory search → repository search → código fuente relevante
```

No recorrer directorios completos ni cargar archivos grandes sin necesidad.

Evitar leer: `*.lock`, `node_modules/`, `dist/`, `build/`, `coverage/`, `.venv/`, `vendor/`, archivos generados.
Inspeccionarlos solo cuando la tarea dependa específicamente de su contenido.

## 7. DISPONIBILIDAD DEL SERVIDOR MCP

Si `codebase-memory-mcp` no responde:

```
1. Revisar scripts del proyecto (ej. /scripts, package.json)
2. Comprobar estado del servidor
3. Iniciarlo con el mecanismo oficial
4. Verificar que el grafo responde
5. Reintentar la operación
```

**Prohibido:**
- Asumir que Memory no está configurado porque el servidor está apagado
- Inventar resultados o comandos del MCP

Si la recuperación falla → usar búsqueda local dirigida y reportar la imposibilidad de sincronizar.

## 8. SCRIPTS DE LIFECYCLE

Si el proyecto usa MCP, debería documentar (en `AGENTS.md` §K) mecanismos equivalentes a:

```
memory:start    memory:stop     memory:status
memory:init     memory:update   memory:rebuild
```

Los nombres varían por proyecto; las capacidades deben existir.
Usar siempre los scripts oficiales antes que comandos manuales.
Si no existen → proponerlos al usuario basándose en la configuración/CLI real instalada. Nunca inventar comandos.

## 9. BOOTSTRAP (Memory vacía)

Si Memory funciona pero no tiene contexto del repo actual:

```
1. Ejecutar memory:init (mecanismo oficial)
2. Generar el grafo inicial
3. Verificar con una búsqueda conocida
4. Solo entonces considerar fiables las búsquedas
```

El bootstrap captura: estructura, módulos, componentes compartidos, entidades, servicios, endpoints y relaciones importantes. No copia código completo.

**Una memoria vacía no demuestra que un elemento no exista.**

## 10. FLUJO OPERATIVO COMPLETO

```
Check Memory
    ↓ (recover/start si es necesario)
Initialize/update si es necesario
    ↓
Search → Trace impact → Inspect source
    ↓
Implement
    ↓
Validate
    ↓
¿Cambio estructural?
   No  → Finish
   Sí  → Update Memory → Verify → Finish
```

## PROHIBICIONES

- Explorar masivamente el repositorio cuando una búsqueda dirigida sea suficiente.
- Crear implementaciones sin buscar equivalentes primero.
- Modificar elementos críticos/compartidos sin analizar impacto.
- Confiar ciegamente en Memory frente al código actual.
- Registrar código no existente o no validado.
- Dejar referencias activas a elementos eliminados o renombrados.
- Contaminar Memory con información trivial.
- Ejecutar rebuild cuando update sea suficiente.
- Inventar resultados, comandos o estado del MCP.
- Dar una búsqueda vacía como fiable si Memory no está inicializado.

## REGLA FINAL

> Search → Trace → Inspect → Change → Validate → Sync.

Memory reduce descubrimiento y contexto. No sustituye la verificación del repositorio.
