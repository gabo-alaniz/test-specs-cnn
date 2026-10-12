# Spec 001: archive-specs

> Fuente: `brief.md`. Tamaño: S (`AGENTS.md` §D).

## Problema y contexto
`specs/` acumula specs cerrados; `status` debe centrarse en lo activo sin que `validate --all` deje de proteger el histórico.

## Usuarios y flujos
Quien mantiene el repo cierra un spec (`speckit close`), completa `retro.md` y lo archiva con `speckit archive <spec>`.

## Criterios de aceptación
- AC-001: Dado un spec `completed`, cuando ejecuto `speckit archive <spec>`, entonces se mueve a `specs/.archive/<spec>/` con todos sus archivos.
- AC-002: Dado un spec que no está `completed` (o cuyo destino ya existe), cuando ejecuto `speckit archive <spec>`, entonces el comando sale con código ≠ 0 y no mueve nada.
- AC-003: Dado un spec archivado, cuando ejecuto `speckit status`, entonces no aparece; cuando ejecuto `validate --all`, entonces sí se valida.

## Alcance
**Incluye:** comando `archive`, carpeta `specs/.archive/`, listado activo separado y validación global del histórico.
**Excluye:** desarchivar, borrar specs.

## Restricciones y datos
Solo stdlib; sin cambios en el schema de `state.json`.

## Notas técnicas (solo size S)
- `cmd_archive` en `.agents/bin/speckit_cli.py`: comprueba `status == "completed"` y el destino, y usa `shutil.move`.
- `status` ignora `.archive/`; `spec_validate.collect_targets --all` recorre activos y archivados.

## Pruebas (solo size S)

| AC | Escenario | Tipo | Comando |
|----|-----------|------|---------|
| AC-001 | spec completed → `.archive/` | unit | `python3 -m unittest tests.test_speckit_cli` |
| AC-002 | spec en curso → error, sin mover | unit | `python3 -m unittest tests.test_speckit_cli` |
| AC-003 | `status` omite y `validate --all` comprueba `.archive/` | unit | `.venv/bin/python -m unittest .agents.tests.test_spec_validate` |
