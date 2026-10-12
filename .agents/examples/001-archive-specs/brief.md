# Brief: archive-specs

> Lo escribe el usuario (5-10 min). El agente lo convierte en `spec.md` después de **una sola ronda** de preguntas.

## 1. Problema
`specs/` crece con cada feature cerrada y `speckit status` y `validate --all` mezclan lo activo con lo histórico.

## 2. Usuario
Quien mantiene el repo (humano o agente), al cerrar cada spec.

## 3. Resultado esperado
Los specs cerrados salen de la vista diaria sin perder el historial: `status` solo lista lo activo.

## 4. Criterios de aceptación
- AC-001: Dado un spec `completed`, cuando ejecuto `speckit archive <spec>`, entonces se mueve a `specs/.archive/<spec>/`.
- AC-002: Dado un spec que no está `completed`, cuando lo archivo, entonces el comando falla y no mueve nada.

## 5. Fuera de alcance
- Desarchivar (se hace con `git mv`).

## 6. Restricciones
Python 3.9+ y solo stdlib.

## 7. Datos
Ninguno nuevo.

## 8. Referencias
`.agents/docs/ROADMAP.md`, fase 3.

## 9. Preguntas abiertas
- ¿`validate --all` debe validar también lo archivado? → Sí; `status` muestra solo activos, pero la validación global no debe ocultar regresiones (AC-003 actualizado).
