# BACKEND & CLOUD ARCHITECTURE RULES
# Propósito: Principios de arquitectura para backends desplegables en cloud o entornos distribuidos.
# Agnóstico al proveedor cloud. Los repos hijo especifican su proveedor en archivos de extensión.

## 1. ARQUITECTURA STATELESS

El backend no almacena estado local. Toda unidad de cómputo es reemplazable:

- **Prohibido** almacenar estado en memoria del proceso entre requests (variables globales mutables, cachés en memoria sin externalizar).
- **Prohibido** escribir archivos en disco del servidor. Los archivos se envían a almacenamiento externo (object storage, CDN).
- Las sesiones y cachés viven en un store externo compartido (cache distribuido, DB).
- Cada instancia del servicio debe poder atender cualquier request sin depender de estado local previo.

## 2. CONFIGURACIÓN POR ENTORNO

- La aplicación se configura exclusivamente mediante variables de entorno.
- No hay valores hardcodeados que cambien entre entornos (desarrollo, staging, producción).
- El código es idéntico en todos los entornos; solo la configuración varía.
- La documentación de variables requeridas vive en `.env.example` con descripción de cada una.

## 3. MIGRACIONES DE BASE DE DATOS

- Todos los cambios de esquema se implementan como migraciones versionadas usando el gestor del proyecto.
- Las migraciones son código: están en control de versiones, son revisables y reproducibles.
- **Prohibido** ejecutar cambios de esquema directamente en consola contra cualquier entorno.
- Las migraciones deben poder ejecutarse en CI/CD sin intervención manual.
- Preferir migraciones no destructivas (añadir columnas, no eliminar en el mismo paso).

## 4. ACCESO A DATOS Y TESTEABILIDAD

- El acceso a datos está abstraído detrás de repositorios o servicios, nunca inline en handlers.
- La capa de acceso a datos es intercambiable: cambiar entre mocks y producción requiere solo una variable de entorno.
- Las implementaciones mock deben simular el comportamiento real: latencia de red, errores transitorios, paginación.
- Los mocks viven en la carpeta designada por el proyecto y no en código de producción.

## 5. RESILIENCIA Y OPERABILIDAD

- Los servicios exponen health checks que permiten a la infraestructura verificar disponibilidad.
- Los errores transitorios (red, dependencias externas) se manejan con reintentos o circuit breakers según corresponda.
- Los timeouts están configurados explícitamente. No hay operaciones de red sin timeout.
- Las dependencias externas opcionales no deben tumbar el servicio si fallan.

## 6. ESCALABILIDAD HORIZONTAL

- No asumir que solo existe una instancia del servicio.
- Las operaciones que requieren exclusividad usan mecanismos de coordinación externos (locks distribuidos, colas).
- Los jobs en background se gestionan con colas o schedulers externos, no con `setTimeout` o threads del proceso.

## PROHIBICIONES

- Estado local mutable entre requests.
- Archivos en disco del servidor (fuera de almacenamiento externo).
- Cambios de esquema sin migración versionada.
- Configuración hardcodeada por entorno.
- Queries de DB directas fuera de la capa de acceso a datos.
- Dependencias externas sin timeout configurado.

## REGLA FINAL

> Stateless → Configuración por entorno → Migraciones como código → Acceso a datos testeable → Resiliente por diseño.

El backend debe poder reemplazar cualquier instancia sin pérdida de estado ni interrupción del servicio.
