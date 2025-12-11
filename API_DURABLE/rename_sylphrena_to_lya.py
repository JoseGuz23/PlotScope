#!/usr/bin/env python
"""
Script para reemplazar todas las referencias de 'Sylphrena' por 'LYA'
"""
import os
import re
from pathlib import Path

def replace_in_file(filepath):
    """Reemplaza Sylphrena por LYA en un archivo."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Reemplazos case-sensitive
        content = content.replace('SYLPHRENA', 'LYA')
        content = content.replace('Sylphrena', 'LYA')
        content = content.replace('sylphrena', 'lya')

        # Si hubo cambios, escribir
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] Actualizado: {filepath.name}")
            return True
        else:
            print(f"[SKIP] Sin cambios: {filepath.name}")
            return False

    except Exception as e:
        print(f"[ERROR] Error en {filepath}: {e}")
        return False

def main():
    """Procesa todos los archivos Python en el directorio."""
    base_dir = Path(__file__).parent

    # Lista de archivos a procesar
    files_to_process = list(base_dir.rglob('*.py'))

    print(f"Encontrados {len(files_to_process)} archivos Python")
    print("=" * 70)

    updated_count = 0

    for filepath in files_to_process:
        # Evitar procesar este script
        if filepath.name == 'rename_sylphrena_to_lya.py':
            continue

        if replace_in_file(filepath):
            updated_count += 1

    print("=" * 70)
    print(f"Proceso completado: {updated_count} archivos actualizados")

if __name__ == "__main__":
    main()
