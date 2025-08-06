#!/usr/bin/env python3
"""
Script para corregir automáticamente los archivos de flujogramas:
1. Eliminar marcadores "🔍 Fragmento 1:"
2. Corregir referencias al reglamento
3. Mejorar formato y consistencia
"""

import os
import glob
import re

def corregir_archivo_flujograma(filepath):
    """Corrige un archivo de flujograma individual"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Guardar contenido original para comparación
        original = contenido
        
        # 1. Eliminar marcadores de fragmento
        contenido = re.sub(r'🔍 Fragmento \d+:\s*\n?', '', contenido)
        
        # 2. Corregir referencias al reglamento
        contenido = re.sub(r'Reglamento Conjunto 20\d{2}', 'Reglamento de Emergencia JP-RP-41', contenido)
        contenido = re.sub(r'Reglamento Conjunto establecido en el año 20\d{2}', 'Reglamento de Emergencia JP-RP-41', contenido)
        contenido = re.sub(r'Reglamento Conjunto del 20\d{2}', 'Reglamento de Emergencia JP-RP-41', contenido)
        contenido = re.sub(r'Reglamento Conjunto vigente', 'Reglamento de Emergencia JP-RP-41', contenido)
        contenido = re.sub(r'Reglamento Conjunto actual', 'Reglamento de Emergencia JP-RP-41', contenido)
        
        # 3. Limpiar espacios en blanco excesivos al inicio
        contenido = re.sub(r'^\s*\n+', '', contenido)
        
        # 4. Asegurar que termine con una sola línea nueva
        contenido = contenido.rstrip() + '\n'
        
        # Solo escribir si hay cambios
        if contenido != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(contenido)
            return True, "Archivo corregido"
        else:
            return False, "Sin cambios necesarios"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    # Buscar todos los archivos de flujogramas
    pattern = "**/flujograma*.txt"
    archivos = glob.glob(pattern, recursive=True)
    
    print(f"🔍 Encontrados {len(archivos)} archivos de flujogramas")
    print("=" * 60)
    
    corregidos = 0
    errores = 0
    
    for archivo in archivos:
        archivo_relativo = os.path.relpath(archivo)
        try:
            cambiado, mensaje = corregir_archivo_flujograma(archivo)
            if cambiado:
                print(f"✅ {archivo_relativo}: {mensaje}")
                corregidos += 1
            else:
                print(f"⚪ {archivo_relativo}: {mensaje}")
        except Exception as e:
            print(f"❌ {archivo_relativo}: Error - {str(e)}")
            errores += 1
    
    print("=" * 60)
    print(f"📊 RESUMEN:")
    print(f"   • Archivos corregidos: {corregidos}")
    print(f"   • Sin cambios: {len(archivos) - corregidos - errores}")
    print(f"   • Errores: {errores}")
    print(f"   • Total procesados: {len(archivos)}")

if __name__ == "__main__":
    main()
