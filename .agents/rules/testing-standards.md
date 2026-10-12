# TESTING STANDARDS
# Propósito: Estándares de pruebas automatizadas agnósticos al framework.
# Los repos hijo especifican su framework de testing en su configuración.

## 1. PRINCIPIO GENERAL

- Todo flujo crítico o funcionalidad significativa requiere cobertura de pruebas.
- Las pruebas validan **comportamiento**, no presencia de código.
- No duplicar la misma prueba en múltiples frameworks sin justificación concreta.
- El agente lanza las pruebas autónomamente; no le pide al usuario que las ejecute.

## 2. TIPOS DE PRUEBA Y CUÁNDO USARLOS

### Unit / Integration Tests
Para: lógica de negocio, transformaciones de datos, validaciones, servicios aislados.
Cuando: cualquier función o módulo con lógica no trivial.

### E2E / Acceptance Tests
Para: flujos completos del usuario de punta a punta.
Cuando: criterios de aceptación del Spec que involucren múltiples capas del sistema.

### Contract Tests
Para: interfaces entre servicios desacoplados (APIs, eventos).
Cuando: el proyecto tenga múltiples servicios o frontend/backend desacoplados con contrato formal.

## 3. SELECCIÓN DE FRAMEWORK

Usar **el framework ya presente en el proyecto**. No introducir uno nuevo sin decisión explícita.

Si el proyecto no tiene framework de testing definido → preguntar al usuario antes de elegir.

Criterios de selección cuando hay múltiples frameworks instalados:
1. ¿Ya existe cobertura del flujo en un framework? → Usar ese para mantener consistencia.
2. ¿El tipo de prueba tiene un framework más adecuado? → Usar el más adecuado.
3. ¿Ambos son equivalentes? → Usar el framework principal del proyecto.

**Prohibido** introducir un segundo framework de testing para la misma responsabilidad.

## 4. EJECUCIÓN

- Las pruebas se ejecutan en el entorno oficial del proyecto (Docker, CI, script definido).
- **Prohibido** ejecutar pruebas directamente en el host si el proyecto define un entorno containerizado.
- Usar siempre los scripts oficiales del proyecto para lanzar pruebas.

Si el script retorna error:
```
1. Leer el log completo
2. Identificar la causa raíz
3. Corregir el código (no el test, salvo que el test esté incorrecto)
4. Volver a ejecutar
5. Repetir hasta exit code = 0
```

## 5. CALIDAD DE LAS PRUEBAS

- Los tests prueban el contrato (qué hace), no la implementación (cómo lo hace internamente).
- No duplicar pruebas de integración con pruebas unitarias para el mismo comportamiento.
- Los tests son mantenibles: si cambiar la implementación sin cambiar el comportamiento rompe un test, el test está mal escrito.
- No hacer pruebas de implementación interna (verificar que se llamó método X con parámetro Y) cuando se puede verificar el resultado observable.

## 6. COBERTURA

- La cobertura es un indicador, no un objetivo en sí mismo.
- Priorizar cobertura de: flujos críticos de negocio, casos borde conocidos, manejo de errores.
- No perseguir 100% de cobertura a costa de pruebas sin valor.

## REGLA FINAL

> Usar el framework del proyecto → Probar comportamiento → Ejecutar en el entorno oficial → Corregir hasta pasar.

Las pruebas son evidencia de que el sistema hace lo que el Spec dice que debe hacer.
