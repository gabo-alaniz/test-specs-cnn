# BACKEND SECURITY RULES
# Propósito: Precondiciones de seguridad para toda implementación de backend.
# Estas reglas no son opcionales — son requisitos de aceptación.

## 1. SECRETOS Y CONFIGURACIÓN

- **Prohibido** incluir credenciales, tokens, claves de API o secrets en texto plano en el código fuente.
- Toda configuración sensible se inyecta desde variables de entorno o sistemas de secrets management del proyecto.
- **Prohibido** commitear archivos `.env` con valores reales. Solo `.env.example` con placeholders.
- Los archivos de configuración con valores sensibles deben estar en `.gitignore`.

## 2. VALIDACIÓN DE ENTRADA

- Todo endpoint o handler que reciba datos externos **debe validar** antes de procesarlos.
- La validación ocurre en los límites del sistema: no se confía en datos de red, archivos o mensajes sin validar.
- Los errores de validación retornan respuestas claras con el código HTTP apropiado. No exponen detalles internos del sistema.
- La lógica de negocio crítica no depende únicamente de validaciones del frontend.

## 3. AUTENTICACIÓN Y AUTORIZACIÓN

- Toda ruta que acceda a datos protegidos verifica autenticación y autorización antes de ejecutar lógica de negocio.
- No asumir que el contexto de autenticación es válido sin verificarlo explícitamente.
- Los tokens de sesión y credenciales nunca se almacenan en lugares no seguros (localStorage para tokens críticos, logs, cookies sin flags apropiados).

## 4. BASE DE DATOS

- Los esquemas de DB son inmutables sin migración explícita versionada.
- **Prohibido** modificar esquemas directamente en consola o sin archivo de migración.
- Toda migración debe ser reproducible y no destructiva por defecto.
- El acceso a datos usa abstracciones (repositorios, servicios) — no queries directas dispersas en handlers.

## 5. LOGGING Y OBSERVABILIDAD

- **Prohibido** usar `console.log` o equivalentes en código de producción. Usar el logger estructurado del proyecto.
- **Nunca** loguear: contraseñas, tokens de sesión, claves de API, datos PII (nombre completo, email, número de tarjeta, CURP/RFC, etc.).
- Los logs deben ser suficientes para diagnosticar problemas sin exponer información sensible.
- Los errores internos no se exponen raw al cliente. Se loguean internamente y se retorna un mensaje genérico.

## 6. ACCESO A DATOS Y MOCKS

- El acceso a datos se abstrae de forma que el cambio entre mocks y producción requiera únicamente una variable de entorno (`USE_MOCKS=true|false`).
- Los mocks de desarrollo deben imitar el comportamiento real del sistema: latencia, errores, paginación.
- Las fábricas de datos de prueba viven en la carpeta de mocks definida por el proyecto.

## PROHIBICIONES

- Secrets en código fuente o control de versiones.
- Endpoints sin validación de entrada.
- Acceso a recursos protegidos sin verificación de autorización.
- Queries directas a DB fuera de la capa de acceso a datos.
- Logs con información PII o sensible.
- Modificación de esquemas sin migración versionada.

## REGLA FINAL

> Cero secrets en código → Validar toda entrada → Autorizar todo acceso → Logger estructurado → Migraciones versionadas.

La seguridad es una precondición de toda implementación, no una feature posterior.
