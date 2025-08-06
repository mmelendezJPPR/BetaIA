#!/usr/bin/env python3
"""
Script para mejorar la calidad y consistencia de flujogramas
"""

import os
import glob
import re

def mejorar_formato_flujograma(filepath):
    """Mejora el formato de un flujograma específico"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        original = contenido
        
        # 1. Estandarizar títulos principales
        contenido = re.sub(r'^([^#\n]*?)([Ff]lujograma[^:\n]*):?\s*', r'### \2\n\n', contenido, flags=re.MULTILINE)
        
        # 2. Mejorar estructura de pasos numerados simples
        contenido = re.sub(r'^(\d+\.\s+)([^*#\n][^:\n]+):?\s*$', r'#### \1**\2**', contenido, flags=re.MULTILINE)
        
        # 3. Convertir listas simples en formato estructurado
        lines = contenido.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Si es un paso numerado simple, convertirlo en formato mejorado
            if re.match(r'^\d+\.\s+[^*]', stripped) and not '**' in stripped:
                # Extraer número y contenido
                match = re.match(r'^(\d+)\.\s+(.+)', stripped)
                if match:
                    num, texto = match.groups()
                    new_lines.append(f'#### {num}. **{texto}**')
                    # Agregar estructura de decisión si parece apropiado
                    if any(keyword in texto.lower() for keyword in ['evalua', 'verifica', 'revisa', 'analiza']):
                        new_lines.append('   - ¿Se cumple con los requisitos establecidos?')
                        new_lines.append('     - **Sí:** Continuar al siguiente paso')
                        new_lines.append('     - **No:** Solicitar correcciones o denegar')
                        new_lines.append('')
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        contenido = '\n'.join(new_lines)
        
        # 4. Limpiar espacios múltiples y líneas vacías excesivas
        contenido = re.sub(r'\n\s*\n\s*\n+', '\n\n', contenido)
        contenido = re.sub(r'^\s+', '', contenido)
        
        # 5. Asegurar terminación apropiada
        if not contenido.endswith('\n'):
            contenido += '\n'
        
        # Solo escribir si hay cambios significativos
        if len(contenido.strip()) > len(original.strip()) * 0.8 and contenido != original:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(contenido)
            return True, "Formato mejorado"
        else:
            return False, "Sin cambios significativos"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    # Solo procesar algunos archivos específicos que necesitan mejoras
    archivos_objetivo = [
        "**/RespuestasIA_Tomo3/**/flujograma*.txt",
        "**/RespuestasIA_Tomo6/**/flujograma*.txt", 
        "**/RespuestasIA_Tomo7/**/flujograma*.txt",
        "**/RespuestasIA_Tomo9/**/flujograma*.txt",
        "**/RespuestasIA_Tomo11/**/flujograma*.txt"
    ]
    
    todos_archivos = []
    for pattern in archivos_objetivo:
        todos_archivos.extend(glob.glob(pattern, recursive=True))
    
    print(f"🔧 Mejorando formato de {len(todos_archivos)} archivos seleccionados")
    print("=" * 60)
    
    mejorados = 0
    
    for archivo in todos_archivos:
        archivo_relativo = os.path.relpath(archivo)
        try:
            cambiado, mensaje = mejorar_formato_flujograma(archivo)
            if cambiado:
                print(f"✅ {archivo_relativo}: {mensaje}")
                mejorados += 1
            else:
                print(f"⚪ {archivo_relativo}: {mensaje}")
        except Exception as e:
            print(f"❌ {archivo_relativo}: Error - {str(e)}")
    
    print("=" * 60)
    print(f"📊 RESUMEN:")
    print(f"   • Archivos mejorados: {mejorados}")
    print(f"   • Sin cambios: {len(todos_archivos) - mejorados}")
    print(f"   • Total procesados: {len(todos_archivos)}")

if __name__ == "__main__":
    main()
