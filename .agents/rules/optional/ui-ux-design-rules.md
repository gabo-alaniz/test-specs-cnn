# UI/UX DESIGN RULES
# Propósito: Referencia detallada del Design System y protocolo de UI.
# Complementa AGENTS.md §E (Fidelidad de Diseño) y §F (Single Source of Truth).
# Este archivo es el contrato técnico detallado; AGENTS.md contiene los principios.

## 1. PRINCIPIO FUNDAMENTAL

Un componente que funciona pero rompe el Design System **no está terminado**.

La consistencia visual del producto tiene prioridad sobre soluciones locales convenientes.
Si dos elementos cumplen la misma función visual o interactiva → deben usar el mismo componente, token o patrón.

## 2. ARQUITECTURA DEL DESIGN SYSTEM

Todo frontend mantiene una jerarquía centralizada:

```
Design Tokens  (valores primitivos: colores, spacing, tipografía, sombras, radios, z-index, transiciones)
    ↓
UI Primitives  (Button, Input, Badge, Icon...)
    ↓
Shared Components  (Table, Modal, Form, DataView, EmptyState, Toast...)
    ↓
Feature Components  (lógica de dominio específica)
    ↓
Pages / Screens
```

Cada nivel consume solo del nivel inmediatamente inferior. No saltar niveles.
Para cada patrón visual, existe **una única implementación oficial**.

## 3. DESIGN TOKENS

Usar tokens para todos los valores globales:

- colores (semánticos: `primary`, `surface`, `danger`, `text-muted`)
- tipografía (familias, tamaños, pesos)
- spacing (escala de separación)
- radios, bordes, sombras
- breakpoints, z-index, transiciones
- tamaños de componentes

**Prohibido** hardcodear valores visuales cuando exista token equivalente.
Preferir tokens semánticos sobre valores físicos en lógica de componentes.

## 4. ORDEN DE DECISIÓN ANTES DE CREAR UI (Reuse-First)

```
1. ¿Existe mockup/diseño aprobado?            → Respetarlo al 100% (ver §5)
2. ¿Existe componente compartido equivalente? → Usarlo
3. ¿Existe variante del componente?           → Usarla
4. ¿Existe token semántico aplicable?         → Usarlo
5. ¿Hay patrón similar en otra feature?       → Replicarlo
6. ¿El componente es reutilizable?            → Crearlo en shared/
7. ¿Es exclusivo de esta feature?             → Crearlo localmente, sin duplicar estilos globales
```

No crear componentes paralelos para resolver diferencias menores.

## 5. FIDELIDAD AL DISEÑO (MOCKUP COMO LEY)

Cuando existe mockup, wireframe o diseño aprobado, el agente está **OBLIGADO** a respetar:

- Proporciones y dimensiones relativas de elementos
- Jerarquía visual (prominencia, tamaño relativo, peso visual)
- Disposición espacial y flujo de los componentes
- Patrones de interacción definidos
- Todos los estados: vacío, cargando, error, éxito

**Prohibido:**
- Reorganizar elementos por preferencia estética del agente
- Simplificar layouts complejos "para facilitar implementación"
- Omitir elementos visuales del mockup sin notificarlo explícitamente
- Crear "versiones mejoradas" del diseño sin aprobación

**Conflicto mockup ↔ Design System:**
```
→ NO resolver silenciosamente
→ Documentar el conflicto al usuario
→ Esperar decisión
→ Registrar resolución en el MCP
```

**Checklist de fidelidad (pre-entrega):**
- [ ] Cada sección del mockup implementada
- [ ] Proporciones relativas correctas
- [ ] Flujo de navegación respetado
- [ ] Estados vacío/error/carga implementados según diseño

## 6. COMPONENTES COMPARTIDOS

Los siguientes patrones usan **la implementación oficial del proyecto**:

- `Button` y variantes (primary, secondary, danger, ghost, icon)
- `Input` / `FormField`, `Select`, `Checkbox`, `Radio`, `Switch`
- `Table` / sistema de tablas
- `Card`
- `Dialog` / `Modal` / `Drawer`
- `Badge`, `Tabs`, `Pagination`
- `Tooltip` / `Popover`, `DatePicker`
- `Toast` / `Alert` / notificaciones
- `Loading State`, `Empty State`, `Error State`
- Modal de confirmación centralizado (reemplaza `window.confirm`)
- `Search` / `Filter` controls

Las diferencias legítimas se expresan mediante **variantes, parámetros o composición**, nunca mediante componentes duplicados o CSS aislado.

## 7. TABLAS

Las features proporcionan a la tabla oficial:
- definición de columnas
- datos
- acciones por fila
- filtros, sorting, paginación
- estado de selección

**Las features NO redefinen:** header, spacing, typography, borders, hover/selection, loading/empty/error states, responsive behavior.

Si cambiar el diseño global de tablas requiere modificar múltiples pantallas individualmente → la arquitectura es incorrecta.

## 8. FORMULARIOS Y ACCIONES

- Buttons, inputs, selects y controles de validación usan componentes compartidos y variantes oficiales.
- **Prohibido** crear estilos locales para botones, inputs o dialogs "especiales" cuando el componente base puede resolverlo.
- **Prohibido** `window.alert` o `window.confirm` → usar el modal de confirmación centralizado.
- La validación crítica de negocio no depende únicamente del frontend.

## 9. ESTILOS LOCALES (qué sí está permitido)

Los estilos locales de una feature se limitan a:
- layout de la página (grid, flex positioning)
- composición espacial específica del dominio
- visualizaciones de datos propias (gráficas, mapas, diagramas ad-hoc)

No deben redefinir la apariencia de ningún componente compartido.

## 10. VARIANTES Y COMPOSICIÓN

- Crear variantes solo cuando representen un patrón **reutilizable**.
- No crear variantes para resolver excepciones estéticas aisladas.
- Para componentes complejos: preferir composición sobre múltiples flags booleanos.
- No promover elementos triviales a componentes globales sin beneficio real.

## 11. RESPONSIVE, ACCESIBILIDAD Y THEMING

Los componentes compartidos centralizan:
- responsive behavior
- semantic HTML, ARIA, keyboard navigation, focus management
- contrast, disabled/error states
- theme support (claro/oscuro)

Las features **no degradan** estas capacidades ni implementan estrategias paralelas para el mismo componente.

**Prohibido** mezclar variables de tema claro en tema oscuro y viceversa.

## 12. MODIFICACIÓN DE COMPONENTES COMPARTIDOS

Antes de modificar un componente compartido:
1. Identificar todos sus consumidores (via MCP `trace_path`)
2. Revisar variantes existentes (¿ya existe lo que necesito?)
3. Evaluar compatibilidad con todos los consumidores
4. Ejecutar tests visuales/funcionales relevantes

**Prohibido** modificar un componente global para resolver únicamente un caso local.
Si el cambio es específico de una feature → crear variante o aplicar estilos locales dentro de los límites permitidos.

## 13. CONSISTENCIA ENTRE AGENTES

Asumir que diferentes agentes implementan features distintas en paralelo:
- No introducir estilos paralelos al Design System
- No inventar patrones visuales sin necesidad
- Aplicar decisiones globales en la fuente central, no en la feature
- Mantener equivalencia visual entre módulos equivalentes

## 14. VALIDACIÓN PRE-ENTREGA

Antes de marcar una tarea frontend como completada:

- [ ] Mockup respetado (si existe)
- [ ] Componentes compartidos existentes reutilizados
- [ ] Tokens aplicados (sin valores hardcodeados)
- [ ] Sin duplicación visual
- [ ] Responsive behavior correcto
- [ ] Accesibilidad preservada
- [ ] Estados loading/empty/error implementados
- [ ] Componentes compartidos no regresionados

## PROHIBICIONES

- Duplicar componentes visuales existentes.
- Crear tablas, botones, dialogs o inputs paralelos cuando existe implementación compartida.
- Hardcodear colores, spacing o estilos cuando existen tokens.
- Copiar CSS entre features o módulos.
- Añadir otra UI library o icon library sin decisión explícita.
- Modificar un componente global para resolver un caso local.
- Romper accesibilidad o responsive behavior de los primitives compartidos.
- Usar `!important`, deep selectors o overrides CSS aislados salvo necesidad técnica justificada.

## REGLA FINAL

> Mockup → Componente existente → Variante → Token → Nuevo (shared) → Nuevo (local).

Un componente que funciona pero rompe el Design System no está terminado.
