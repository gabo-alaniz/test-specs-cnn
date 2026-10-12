# FRAMEWORK & STACK RULES
# Propósito: Gobernanza del stack técnico. Aplica a cualquier tecnología.
# Los repos hijo extienden este archivo con secciones específicas de su stack.

## 1. STACK AUTORITATIVO

El stack del proyecto es la única fuente de verdad técnica:

- Respetar frameworks, versiones, ORMs, state managers, UI libraries y paradigmas definidos.
- Antes de implementar: revisar manifiestos de dependencias del proyecto (`package.json`, `pyproject.toml`, `pubspec.yaml`, `go.mod`, etc.) y una implementación similar existente.
- **Prohibido** cambiar frameworks, bases de datos, paradigmas arquitectónicos o versiones mayores sin decisión explícita documentada.
- **Prohibido** hacer upgrades de versiones mayores como efecto secundario de otra tarea.

## 2. ORDEN DE DECISIÓN TÉCNICA

Para resolver cualquier necesidad técnica, seguir este orden sin saltarse pasos:

```
1. Patrón existente en el proyecto
2. Capacidad oficial/nativa del framework instalado
3. Dependencia ya instalada en el proyecto
4. Solución simple compatible con la arquitectura actual
5. Nueva dependencia ← solo si las 4 anteriores no son adecuadas
```

La consistencia del proyecto tiene prioridad sobre la preferencia del agente.

## 3. UNA SOLUCIÓN POR RESPONSABILIDAD

- Mantener una solución principal por responsabilidad: estado, UI, validación, persistencia, HTTP, testing, logging, etc.
- **Prohibido** introducir una segunda librería para resolver el mismo problema que ya resuelve una existente.
- **Prohibido** crear mini-frameworks, wrappers genéricos o abstracciones profundas sin necesidad concreta y reutilizable.
- Nuevas tecnologías estructurales requieren decisión arquitectónica explícita (ADR si el proyecto los usa).

## 4. FRAMEWORK-FIRST

- Usar APIs oficiales, modernas y no deprecadas de la versión instalada.
- No recrear capacidades que el framework ya provee.
- Evitar escape hatches (`unsafe casts`, manipulación directa del DOM, estado global mutable, reflection hacks) salvo justificación técnica explícita.
- No migrar código legacy fuera del alcance de la tarea actual.

## 5. ARQUITECTURA DE CAPAS

- La lógica de negocio debe ser independiente del framework de entrega (HTTP, CLI, UI).
- Controllers, routes y handlers se encargan de: entrada, validación superficial, orquestación y respuesta. No concentran lógica de dominio.
- Respetar los límites y el flujo de dependencias definido por la arquitectura existente.
- Una nueva feature replica la estructura, naming, acceso a datos y manejo de errores de las features equivalentes existentes.

## 6. TIPADO Y CONTRATOS

- Usar el nivel de tipado estricto soportado por el stack del proyecto.
- **Prohibido** silenciar errores de tipo para hacer compilar una implementación.
- Validar datos externos en los límites del sistema (entrada de red, archivos, mensajes).
- Mantener separados modelos de persistencia, dominio, API y UI cuando tengan responsabilidades distintas.
- Cuando frontend y backend estén desacoplados: usar el contrato oficial del proyecto (OpenAPI, GraphQL, Protobuf, JSON Schema, etc.).
- Generar clientes/tipos desde el contrato cuando el stack lo permita. No duplicar DTOs manualmente.

## 7. DEPENDENCIAS

Antes de agregar cualquier dependencia nueva:

1. Confirmar que no existe solución equivalente ya instalada.
2. Confirmar que el framework no lo resuelve nativamente.
3. Verificar compatibilidad con las versiones actuales del proyecto.
4. Evaluar mantenimiento activo, seguridad y coste de complejidad.
5. **Prohibido** añadir dependencias arquitectónicas para problemas triviales.
6. No modificar lock files manualmente.

## 8. IMPLEMENTACIÓN

Antes de implementar una feature:

- Buscar una feature equivalente en el proyecto para replicar el patrón.
- No introducir una arquitectura local diferente a la del proyecto.
- Si la solución requiere romper una regla del stack → detener, explicitar el conflicto, esperar decisión.

## 9. VALIDACIÓN PRE-ENTREGA

Ejecutar según lo que aplique al stack del proyecto:

- formatter / linter
- type checking
- unit/integration tests afectados
- build
- diagnósticos específicos del framework

**Prohibido** afirmar que una validación pasó si no fue ejecutada. Reportar cualquier validación requerida que no haya podido ejecutarse.

## 10. EXTENSIÓN POR REPOS HIJO

Los repos hijo documentan su stack concreto en `.agents/rules/stack-<technology>.md`, por ejemplo:

- `stack-nextjs.md` — reglas específicas de Next.js
- `stack-python-fastapi.md` — reglas específicas de FastAPI
- `stack-flutter.md` — reglas específicas de Flutter

Estos archivos extienden las reglas de este documento. Nunca las contradicen.

## PROHIBICIONES

Salvo decisión explícita documentada:

- No cambiar el stack.
- No introducir librerías paralelas para la misma responsabilidad.
- No actualizar versiones mayores incidentalmente.
- No crear abstracciones especulativas sin uso concreto.
- No usar APIs deprecadas en código nuevo.
- No duplicar contratos que puedan generarse.
- No ignorar patrones existentes por preferencia del agente.
- No convertir una feature en una migración arquitectónica.

## REGLA FINAL

> Patrón existente → Framework nativo → Dependencia instalada → Solución simple → Nueva dependencia.

Una solución técnicamente válida que fragmenta la arquitectura existente no es una solución aceptable.
