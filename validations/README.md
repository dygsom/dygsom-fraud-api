# Validations

Esta carpeta contiene scripts y reportes de validación del código, aislados del código principal de producción.

## Contenido

- `verify_day2.py` - Script de verificación del checklist del Día 2
- `CODE_QUALITY_REPORT.md` - Reporte de calidad de código (Black, Flake8, Type hints)

## Uso

```bash
# Ejecutar verificación del Día 2
docker compose exec api python validations/verify_day2.py

# Ver reporte de calidad
cat validations/CODE_QUALITY_REPORT.md
```

## Nota

Estos archivos son para validación y testing del proceso de desarrollo. No forman parte del código de producción.
