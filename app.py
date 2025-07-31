from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_cors import CORS
import os
import re
import sys
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI

# CONFIGURACIÓN BETA - FECHA DE EXPIRACIÓN
FECHA_EXPIRACION_BETA = datetime.now() + timedelta(minutes=10)  # 10 minutos para pruebas
def formatear_fecha_espanol(fecha):
    """Convierte una fecha al formato español"""
    meses_espanol = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }

    if isinstance(fecha, datetime):
        dia = fecha.day
        mes = meses_espanol[fecha.month]
        año = fecha.year
        hora = fecha.strftime('%H:%M')
        return f"{dia} de {mes} de {año} a las {hora}"
    else:
        dia = fecha.day
        mes = meses_espanol[fecha.month]
        año = fecha.year
        return f"{dia} de {mes} de {año}"

    
    dia = fecha.day
    mes = meses_espanol[fecha.month]
    año = fecha.year
    
    return f"{dia} de {mes} de {año}"

def verificar_beta_activa():
    """Verifica si la versión beta sigue activa"""
    ahora = datetime.now()
    
    if ahora <= FECHA_EXPIRACION_BETA:
        tiempo_restante = FECHA_EXPIRACION_BETA - ahora
        minutos_restantes = int(tiempo_restante.total_seconds() / 60)
        return True, minutos_restantes
    else:
        return False, 0
    
# Configuración de la aplicación Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Para sesiones seguras
CORS(app)

# Configurar MIME types para archivos estáticos
import mimetypes
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')

# Asegurar que estamos en el directorio correcto
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Cargar variables de entorno y cliente
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Lista de palabras clave legales para detección
palabras_legales = [
    'permiso', 'planificación', 'construcción', 'zonificación', 'desarrollo',
    'urbanización', 'reglamento', 'licencia', 'certificación', 'calificación',
    'tomo', 'junta', 'planificación', 'ambiental', 'infraestructura',
    'conservación', 'histórico', 'querella', 'edificabilidad', 'lotificación'
]

# Función para cargar glosario (si existe)
def cargar_glosario():
    ruta_glosario = os.path.join("data", "glosario.txt")
    if os.path.exists(ruta_glosario):
        try:
            with open(ruta_glosario, "r", encoding="utf-8") as f:
                contenido = f.read()
            print(f"✅ Glosario cargado: {len(contenido)} caracteres, {len(contenido.split('**'))} términos aprox.")
            return contenido
        except Exception as e:
            print(f"❌ Error cargando glosario: {e}")
            return ""
    else:
        print(f"⚠️ Glosario no encontrado en: {ruta_glosario}")
        return ""

glosario = cargar_glosario()

# Función para obtener información completa de todos los tomos
def obtener_titulos_tomos():
    """Devuelve información completa sobre todos los tomos del Reglamento Conjunto 2020"""
    return """
**ÍNDICE COMPLETO DE LOS 11 TOMOS DEL REGLAMENTO CONJUNTO 2020**

**TOMO 1:** Sistema de Evaluación y Tramitación de Permisos para el Desarrollo
- Enfoque: Procedimientos administrativos, transparencia y uniformidad del sistema unificado
- Agencias: Junta de Planificación (JP), Oficina de Gerencia de Permisos (OGPe), Municipios Autónomos, Profesionales Autorizados

**TOMO 2:** Disposiciones Generales  
- Enfoque: Procedimientos administrativos para permisos, consultas, certificaciones y documentos ambientales
- Aplicación: Ley 38-2017 LPAU, determinaciones finales y trámites que afecten operación de negocios

**TOMO 3:** Permisos para Desarrollo y Negocios
- Enfoque: Tipos de permisos, procedimientos para desarrollo de proyectos y operación de negocios
- Incluye: Permisos de medio ambiente, flujogramas de cambios de calificación

**TOMO 4:** Licencias y Certificaciones
- Enfoque: Diversos tipos de licencias y certificaciones requeridas para negocios y operaciones
- Regulación: Operaciones comerciales e industriales específicas

**TOMO 5:** Urbanización y Lotificación
- Enfoque: Proyectos de urbanización, procesos de lotificación y clasificaciones de terrenos
- Regulación: Desarrollo residencial y comercial, subdivisión de terrenos

**TOMO 6:** Distritos de Calificación
- Enfoque: Zonificación, clasificación de distritos y usos permitidos por zona
- Regulación: Ordenamiento territorial y usos de suelo

**TOMO 7:** Procesos
- Enfoque: Procedimientos específicos para diversos tipos de trámites y procesos administrativos
- Regulación: Metodologías y secuencias de tramitación

**TOMO 8:** Edificabilidad
- Enfoque: Regulaciones sobre construcción, densidad y parámetros de edificación
- Regulación: Altura, retiros, cabida y otros parámetros constructivos

**TOMO 9:** Infraestructura y Ambiente
- Enfoque: Requisitos de infraestructura, consideraciones ambientales y sostenibilidad
- Regulación: Servicios públicos, impacto ambiental, conservación

**TOMO 10:** Conservación Histórica
- Enfoque: Protección del patrimonio histórico, sitios arqueológicos y edificaciones históricas
- Regulación: Preservación cultural y arquitectónica

**TOMO 11:** Querellas
- Enfoque: Procedimientos para revisiones administrativas, querellas, multas y auditorías
- Regulación: Recursos administrativos y procesos de impugnación ante la División de Revisiones Administrativas de la OGPe

**RECURSOS ADICIONALES:**
- Glosario de términos especializados
- Tablas de cabida por distritos
- Flujogramas de procesos específicos
- Resoluciones de la Junta de Planificación
- Documentación de sitios históricos y terrenos públicos
"""

# Diccionario para mantener conversaciones por sesión
conversaciones = {}

def get_conversation_id():
    """Obtiene o crea un ID de conversación para la sesión actual"""
    if 'conversation_id' not in session:
        session['conversation_id'] = str(uuid.uuid4())
    return session['conversation_id']

def inicializar_conversacion(conversation_id):
    """Inicializa una nueva conversación"""
    if conversation_id not in conversaciones:
        conversaciones[conversation_id] = [
            {"role": "system", "content": """Eres Agente de Planificación, un asistente especializado altamente inteligente en leyes de planificación de Puerto Rico. 

CARACTERÍSTICAS:
- Analiza profundamente las preguntas del usuario
- Proporciona respuestas completas y detalladas
- Usa contexto de múltiples fuentes cuando es necesario
- Explica conceptos legales de manera clara
- Si es una pregunta legal/planificación, usa SOLO el texto proporcionado
- Si es pregunta general, responde libremente como un asistente avanzado
- Siempre sé útil, preciso y profesional
- Recomendar y corregir al usuario como hacer la pregunta correctamente

CAPACIDADES ESPECIALES:
- Puedes analizar y comparar información entre diferentes tomos
- Puedes hacer resúmenes y síntesis
- Puedes explicar procedimientos y procesos
- Puedes identificar relaciones entre diferentes regulaciones
- TIENES ACCESO COMPLETO AL GLOSARIO DE TÉRMINOS LEGALES (Tomo 12)

CONOCIMIENTO SOBRE LOS TOMOS:
Hay en total 11 tomos del Reglamento Conjunto 2020 + Glosario:
**Favor de mencionar los titulos de los tomos**
- Tomo 1: Sistema de Evaluación y Tramitación de Permisos para el Desarrollo
- Tomo 2: Disposiciones Generales
- Tomo 3: Permisos para Desarrollo y Negocios
- Tomo 4: Licencias y Certificaciones
- Tomo 5: Urbanización y Lotificación
- Tomo 6: Distritos de Calificación
- Tomo 7: Procesos
- Tomo 8: Edificabilidad
- Tomo 9: Infraestructura y Ambiente
- Tomo 10: Conservación Histórica
- Tomo 11: Querellas
- Glosario de términos especializados (Tomo 12) - COMPLETAMENTE DISPONIBLE

GLOSARIO DISPONIBLE:
- Contiene definiciones oficiales de todos los términos legales
- Puedes buscar y explicar cualquier término técnico
- Siempre consulta el glosario para preguntas sobre definiciones
- El glosario incluye categorías como: términos de planificación, términos especializados, etc.

Cuando el usuario pregunte por títulos de tomos, índice, o definiciones, proporciona la información completa disponible."""}
        ]

def buscar_en_glosario(termino):
    """Busca definiciones específicas en el glosario con múltiples estrategias"""
    if not glosario:
        return None
    
    termino_lower = termino.lower().strip()
    lineas = glosario.split('\n')
    definiciones_encontradas = []
    
    i = 0
    while i < len(lineas):
        linea = lineas[i].strip()
        
        # Buscar líneas que contengan términos (formatos: **Término**: o **TÉRMINO**: )
        if linea.startswith('**') and ('**:' in linea):
            # Extraer el término según el formato
            termino_glosario = ""
            if linea.startswith('**TÉRMINO**:'):
                # Formato **TÉRMINO**: Zona Costanera
                termino_glosario = linea.replace('**TÉRMINO**:', '').strip().lower()
            elif '**:' in linea:
                # Formato **Término**:
                inicio = linea.find('**') + 2
                fin = linea.find('**:', inicio)
                if fin > inicio:
                    termino_glosario = linea[inicio:fin].strip().lower()
            # Solo procesar si se extrajo un término válido
            if termino_glosario:
                
                # Verificar coincidencia con múltiples estrategias
                coincide = False
                
                # 1. Coincidencia exacta (prioridad máxima)
                if termino_lower == termino_glosario:
                    coincide = True
                # 2. Coincidencia por contención (solo si es significativa)
                elif len(termino_lower) >= 5 and (termino_lower in termino_glosario or termino_glosario in termino_lower):
                    # Verificar que la contención sea significativa
                    if len(termino_lower) / len(termino_glosario) >= 0.3 or len(termino_glosario) / len(termino_lower) >= 0.3:
                        coincide = True
                # 3. Para términos compuestos, verificar palabras clave
                elif ' ' in termino_lower and len(termino_lower) >= 5:
                    palabras_termino = [p for p in termino_lower.split() if len(p) > 2]
                    palabras_glosario = termino_glosario.split()
                    coincidencias = 0
                    for palabra in palabras_termino:
                        for palabra_glos in palabras_glosario:
                            if palabra == palabra_glos or (len(palabra) > 4 and palabra in palabra_glos):
                                coincidencias += 1
                                break
                    # Requerir coincidencia de al menos 80% de las palabras clave
                    if coincidencias >= max(1, len(palabras_termino) * 0.8):
                        coincide = True
                
                if coincide:
                    # Construir la definición completa
                    definicion_completa = linea + '\n'  # Título
                    
                    # Buscar las líneas de definición
                    j = i + 1
                    definicion_encontrada = False
                    contenido_definicion = []
                    
                    while j < len(lineas) and j < i + 10:  # Máximo 10 líneas hacia adelante
                        linea_sig = lineas[j].strip()
                        
                        # Si encontramos otra definición de término, parar
                        if linea_sig.startswith('**TÉRMINO**:') or (linea_sig.startswith('**') and '**:' in linea_sig and not linea_sig.startswith('**CATEGORÍA') and not linea_sig.startswith('**DEFINICIÓN')):
                            break
                        # Si encontramos una categoría al final, la incluimos y paramos
                        elif linea_sig.startswith('**CATEGORÍA'):
                            contenido_definicion.append(linea_sig)
                            break
                        # Si la línea tiene contenido sustancial, la agregamos
                        elif linea_sig and len(linea_sig) > 3:
                            contenido_definicion.append(linea_sig)
                            definicion_encontrada = True
                        
                        j += 1
                    
                    # Solo agregar si encontramos una definición válida
                    if contenido_definicion:
                        definicion_texto = '\n'.join(contenido_definicion)
                        definicion_completa += definicion_texto
                        
                        if len(definicion_completa.strip()) > 10:
                            definiciones_encontradas.append(definicion_completa.strip())
                            
                            # Limitar a 5 definiciones para evitar respuestas muy largas
                            if len(definiciones_encontradas) >= 5:
                                break
        
        i += 1
    
    return definiciones_encontradas if definiciones_encontradas else None

def buscar_multiples_terminos(terminos):
    """Busca múltiples términos relacionados en el glosario"""
    resultados = {}
    
    for termino in terminos:
        definiciones = buscar_en_glosario(termino)
        if definiciones:
            resultados[termino] = definiciones
    
    return resultados

def buscar_flujograma(tipo_flujograma, tomo=None):
    """Busca flujogramas específicos por tipo y tomo"""
    tipos_flujograma = {
        'terrenos': 'flujogramaTerrPublicos',
        'calificacion': 'flujogramaCambiosCalificacion', 
        'historicos': 'flujogramaSitiosHistoricos'
    }
    
    if tipo_flujograma not in tipos_flujograma:
        return None
    
    nombre_archivo = tipos_flujograma[tipo_flujograma]
    resultados = []
    
    def buscar_archivo_flujograma(tomo_num, nombre_archivo):
        """Busca el archivo de flujograma en las diferentes estructuras de carpetas"""
        # Estructura para tomos 1-7 (archivos directos)
        ruta_directa = f"data/RespuestasParaChatBot/RespuestasIA_Tomo{tomo_num}/{nombre_archivo}_Tomo_{tomo_num}.txt"
        
        # Estructura para tomos 8-11 (carpetas organizadas)
        ruta_subcarpeta = f"data/RespuestasParaChatBot/RespuestasIA_Tomo{tomo_num}/Flujogramas/{nombre_archivo}_Tomo_{tomo_num}.txt"
        
        for ruta in [ruta_directa, ruta_subcarpeta]:
            try:
                with open(ruta, 'r', encoding='utf-8') as file:
                    contenido = file.read()
                    if contenido.strip():
                        return contenido
            except FileNotFoundError:
                continue
        return None
    
    # Si especifica un tomo, buscar solo en ese tomo
    if tomo:
        contenido = buscar_archivo_flujograma(tomo, nombre_archivo)
        if contenido:
            resultados.append(f"**FLUJOGRAMA TOMO {tomo} - {tipo_flujograma.upper()}:**\n{contenido}")
    else:
        # Mostrar resumen de TODOS los tomos disponibles
        resumen_tomos = []
        for tomo_num in range(1, 12):
            contenido = buscar_archivo_flujograma(tomo_num, nombre_archivo)
            if contenido:
                # Tomar las primeras líneas para el resumen
                primeras_lineas = '\n'.join(contenido.split('\n')[:4])
                resumen_tomos.append(f"**TOMO {tomo_num}:** {primeras_lineas}...")
        
        if resumen_tomos:
            resultados.append(f"🔄 **FLUJOGRAMAS DISPONIBLES - {tipo_flujograma.upper()}:**\n\n" + '\n\n'.join(resumen_tomos))
            resultados.append(f"\n💡 *Para ver un flujograma completo, especifica el tomo: 'flujograma {tipo_flujograma} tomo 4'*")
    
    return resultados if resultados else None

def buscar_tabla_cabida(tomo=None):
    """Busca tablas de cabida por tomo"""
    resultados = []
    
    def buscar_archivo_tabla(tomo_num):
        """Busca el archivo de tabla de cabida en las diferentes estructuras de carpetas"""
        # Estructura para tomos 1-7 (archivos directos)
        ruta_directa = f"data/RespuestasParaChatBot/RespuestasIA_Tomo{tomo_num}/TablaCabida_Tomo_{tomo_num}.txt"
        
        # Estructura para tomos 8-11 (carpetas organizadas)
        ruta_subcarpeta = f"data/RespuestasParaChatBot/RespuestasIA_Tomo{tomo_num}/Tablas/TablaCabida_Tomo_{tomo_num}.txt"
        
        for ruta in [ruta_directa, ruta_subcarpeta]:
            try:
                with open(ruta, 'r', encoding='utf-8') as file:
                    contenido = file.read()
                    if contenido.strip():
                        return contenido
            except FileNotFoundError:
                continue
        return None
    
    if tomo:
        contenido = buscar_archivo_tabla(tomo)
        if contenido:
            resultados.append(f"**TABLA DE CABIDA - TOMO {tomo}:**\n{contenido}")
    else:
        # Buscar en TODOS los tomos y mostrar un resumen
        resumen_tomos = []
        for tomo_num in range(1, 12):
            contenido = buscar_archivo_tabla(tomo_num)
            if contenido:
                # Extraer solo las primeras líneas para el resumen
                primeras_lineas = '\n'.join(contenido.split('\n')[:5])
                resumen_tomos.append(f"**TOMO {tomo_num}:** {primeras_lineas}...")
        
        if resumen_tomos:
            resultados.append("📊 **RESUMEN DE TABLAS DE CABIDA DISPONIBLES:**\n\n" + '\n\n'.join(resumen_tomos))
            resultados.append("\n💡 *Para ver una tabla completa, especifica el tomo: 'tabla de cabida tomo 3'*")
    
    return resultados if resultados else None

def buscar_resoluciones(tomo=None, tema=None):
    """Busca resoluciones por tomo y tema"""
    resultados = []
    
    def buscar_archivo_resoluciones(tomo_num):
        """Busca el archivo de resoluciones en las diferentes estructuras de carpetas"""
        # Estructura para tomos 1-7 (archivos directos)
        ruta_directa = f"data/RespuestasParaChatBot/RespuestasIA_Tomo{tomo_num}/Resoluciones_Tomo_{tomo_num}.txt"
        
        # Estructura para tomos 8-11 (carpetas organizadas)
        ruta_subcarpeta = f"data/RespuestasParaChatBot/RespuestasIA_Tomo{tomo_num}/Resoluciones/Resoluciones_Tomo_{tomo_num}.txt"
        
        for ruta in [ruta_directa, ruta_subcarpeta]:
            try:
                with open(ruta, 'r', encoding='utf-8') as file:
                    contenido = file.read()
                    if contenido.strip():
                        return contenido
            except FileNotFoundError:
                continue
        return None
    
    if tomo:
        contenido = buscar_archivo_resoluciones(tomo)
        if contenido:
            if tema:
                # Filtrar por tema si se especifica
                lineas = contenido.split('\n')
                lineas_relevantes = [linea for linea in lineas if tema.lower() in linea.lower()]
                if lineas_relevantes:
                    contenido_filtrado = '\n'.join(lineas_relevantes[:10])  # Máximo 10 líneas
                    resultados.append(f"**RESOLUCIONES - TOMO {tomo} - TEMA: {tema.upper()}:**\n{contenido_filtrado}")
            else:
                resultados.append(f"**RESOLUCIONES - TOMO {tomo}:**\n{contenido[:800]}...")
    else:
        # Mostrar resumen de TODOS los tomos disponibles
        resumen_tomos = []
        for tomo_num in range(1, 12):
            contenido = buscar_archivo_resoluciones(tomo_num)
            if contenido:
                # Extraer las primeras líneas para el resumen
                primeras_lineas = '\n'.join(contenido.split('\n')[:3])
                resumen_tomos.append(f"**TOMO {tomo_num}:** {primeras_lineas}...")
        
        if resumen_tomos:
            resultados.append("📋 **RESUMEN DE RESOLUCIONES DISPONIBLES:**\n\n" + '\n\n'.join(resumen_tomos))
            resultados.append("\n💡 *Para ver resoluciones completas, especifica el tomo: 'resoluciones tomo 5'*")
    
    return resultados if resultados else None

def generar_indice_completo():
    """Genera un índice completo de todos los recursos disponibles por tomo"""
    indice = "📚 **ÍNDICE COMPLETO DE RECURSOS DISPONIBLES**\n\n"
    
    recursos_encontrados = {
        'flujogramas_terrenos': [],
        'flujogramas_calificacion': [],
        'flujogramas_historicos': [],
        'tablas_cabida': [],
        'resoluciones': []
    }
    
    def verificar_archivo_existe(tomo_num, nombre_archivo, subcarpeta=""):
        """Verifica si un archivo existe en cualquiera de las estructuras de carpetas"""
        if subcarpeta:
            # Estructura para tomos 8-11 (carpetas organizadas)
            ruta_subcarpeta = f"data/RespuestasParaChatBot/RespuestasIA_Tomo{tomo_num}/{subcarpeta}/{nombre_archivo}_Tomo_{tomo_num}.txt"
        else:
            ruta_subcarpeta = None
            
        # Estructura para tomos 1-7 (archivos directos)
        ruta_directa = f"data/RespuestasParaChatBot/RespuestasIA_Tomo{tomo_num}/{nombre_archivo}_Tomo_{tomo_num}.txt"
        
        rutas = [ruta_directa] + ([ruta_subcarpeta] if ruta_subcarpeta else [])
        
        for ruta in rutas:
            try:
                with open(ruta, 'r', encoding='utf-8') as file:
                    if file.read().strip():
                        return True
            except FileNotFoundError:
                continue
        return False
    
    # Verificar qué recursos existen en cada tomo
    for tomo_num in range(1, 12):
        # Verificar flujogramas
        if verificar_archivo_existe(tomo_num, 'flujogramaTerrPublicos', 'Flujogramas'):
            recursos_encontrados['flujogramas_terrenos'].append(tomo_num)
        if verificar_archivo_existe(tomo_num, 'flujogramaCambiosCalificacion', 'Flujogramas'):
            recursos_encontrados['flujogramas_calificacion'].append(tomo_num)
        if verificar_archivo_existe(tomo_num, 'flujogramaSitiosHistoricos', 'Flujogramas'):
            recursos_encontrados['flujogramas_historicos'].append(tomo_num)
        
        # Verificar tablas de cabida
        if verificar_archivo_existe(tomo_num, 'TablaCabida', 'Tablas'):
            recursos_encontrados['tablas_cabida'].append(tomo_num)
        
        # Verificar resoluciones
        if verificar_archivo_existe(tomo_num, 'Resoluciones', 'Resoluciones'):
            recursos_encontrados['resoluciones'].append(tomo_num)
    
    # Construir el índice
    indice += "🔄 **FLUJOGRAMAS DISPONIBLES:**\n"
    indice += f"• **Terrenos Públicos:** Tomos {', '.join(map(str, recursos_encontrados['flujogramas_terrenos']))}\n"
    indice += f"• **Cambios de Calificación:** Tomos {', '.join(map(str, recursos_encontrados['flujogramas_calificacion']))}\n"
    indice += f"• **Sitios Históricos:** Tomos {', '.join(map(str, recursos_encontrados['flujogramas_historicos']))}\n\n"
    
    indice += "📊 **TABLAS DE CABIDA DISPONIBLES:**\n"
    indice += f"• Tomos {', '.join(map(str, recursos_encontrados['tablas_cabida']))}\n\n"
    
    indice += "📋 **RESOLUCIONES DISPONIBLES:**\n"
    indice += f"• Tomos {', '.join(map(str, recursos_encontrados['resoluciones']))}\n\n"
    
    indice += "💡 **CÓMO USAR:**\n"
    indice += "• Para flujogramas: 'flujograma terrenos tomo 3'\n"
    indice += "• Para tablas: 'tabla de cabida tomo 5'\n"
    indice += "• Para resoluciones: 'resoluciones tomo 7'\n"
    indice += "• Para todo de un tomo: 'recursos del tomo 2'"
    
    return indice

def procesar_pregunta_glosario(entrada):
    """Procesa preguntas específicas del glosario"""
    entrada_lower = entrada.lower()
    
    # Detectar preguntas de comparación/diferencia
    if any(palabra in entrada_lower for palabra in ['diferencia', 'diferencias', 'comparar', 'comparación']):
        # Buscar patrones como "diferencia entre X y Y"
        patrones_comparacion = [
            r'diferencias?\s+entre\s+(.+?)\s+y\s+(.+?)[\?]?',
            r'comparar\s+(.+?)\s+y\s+(.+?)[\?]?',
            r'qué\s+diferencia\s+hay\s+entre\s+(.+?)\s+y\s+(.+?)[\?]?'
        ]
        
        for patron in patrones_comparacion:
            match = re.search(patron, entrada_lower)
            if match:
                termino1 = match.group(1).strip()
                termino2 = match.group(2).strip()
                
                # Buscar ambos términos
                def1 = buscar_en_glosario(termino1)
                def2 = buscar_en_glosario(termino2)
                
                if def1 or def2:
                    respuesta = f"📊 **Comparación entre '{termino1}' y '{termino2}':**\n\n"
                    
                    if def1:
                        respuesta += f"**🔹 {termino1.title()}:**\n"
                        for definicion in def1:
                            respuesta += f"{definicion}\n\n"
                    else:
                        respuesta += f"**🔹 {termino1.title()}:** No encontrado en el glosario.\n\n"
                    
                    if def2:
                        respuesta += f"**🔹 {termino2.title()}:**\n"
                        for definicion in def2:
                            respuesta += f"{definicion}\n\n"
                    else:
                        respuesta += f"**🔹 {termino2.title()}:** No encontrado en el glosario.\n\n"
                    
                    respuesta += "---\n💡 *Información extraída del Glosario - Tomo 12*"
                    return respuesta
    
    # Patrones comunes para preguntas de definiciones (más amplios)
    patrones_definicion = [
        r'qu[eé]\s+es\s+(.+?)[\?]?',
        r'define\s+(.+?)[\?]?',
        r'definici[oó]n\s+de\s+(.+?)[\?]?',
        r'significado\s+de\s+(.+?)[\?]?',
        r'explica\s+(.+?)[\?]?',
        r'explícame\s+(.+?)[\?]?',
        r'(.+?)\s+significa[\?]?',
        r'(.+?)\s+es[\?]?'
    ]
    
    for patron in patrones_definicion:
        match = re.search(patron, entrada_lower)
        if match:
            termino = match.group(1).strip()
            
            # Limpiar el término de palabras comunes
            palabras_eliminar = ['qué es', 'que es', 'el ', 'la ', 'los ', 'las ', 'un ', 'una ', 'significa', 'es']
            for palabra in palabras_eliminar:
                termino = termino.replace(palabra, '').strip()
            
            if termino:  # Solo buscar si queda algo después de limpiar
                definiciones = buscar_en_glosario(termino)
                
                if definiciones:
                    respuesta = f"📚 **Definición(es) encontrada(s) para '{termino.title()}':**\n\n"
                    for i, definicion in enumerate(definiciones, 1):
                        respuesta += f"**{i}.** {definicion}\n\n"
                    
                    # Agregar información del glosario
                    respuesta += "---\n💡 *Información extraída del Glosario - Tomo 12*"
                    return respuesta
    
    # Si no se encuentra con patrones, intentar buscar palabras clave directamente
    palabras_clave = [palabra for palabra in entrada.split() if len(palabra) > 3]
    for palabra in palabras_clave:
        definiciones = buscar_en_glosario(palabra)
        if definiciones:
            respuesta = f"📚 **Término relacionado encontrado: '{palabra.title()}':**\n\n"
            for i, definicion in enumerate(definiciones[:2], 1):  # Máximo 2 para búsqueda automática
                respuesta += f"**{i}.** {definicion}\n\n"
            
            respuesta += "---\n💡 *Información extraída del Glosario - Tomo 12*"
            return respuesta
    
    return None

def detectar_consulta_especifica(entrada):
    """Detecta consultas específicas sobre recursos estructurados"""
    entrada_lower = entrada.lower()
    
    # Detectar solicitud de índice completo
    if any(palabra in entrada_lower for palabra in ['índice', 'indice', 'lista completa', 'todos los recursos', 'qué recursos', 'recursos disponibles']):
        return {'tipo': 'indice_completo'}
    
    # Detectar búsqueda de flujogramas
    if any(palabra in entrada_lower for palabra in ['flujograma', 'proceso', 'trámite', 'procedimiento']):
        if any(palabra in entrada_lower for palabra in ['terreno', 'terrenos', 'público', 'públicos']):
            return {'tipo': 'flujograma', 'subtipo': 'terrenos'}
        elif any(palabra in entrada_lower for palabra in ['calificación', 'cambio', 'cambios']):
            return {'tipo': 'flujograma', 'subtipo': 'calificacion'}
        elif any(palabra in entrada_lower for palabra in ['histórico', 'historicos', 'sitio', 'sitios']):
            return {'tipo': 'flujograma', 'subtipo': 'historicos'}
    
    # Detectar búsqueda de tablas de cabida
    if any(palabra in entrada_lower for palabra in ['cabida', 'tabla', 'distrito', 'calificación']):
        if any(palabra in entrada_lower for palabra in ['mínima', 'máxima', 'tabla']):
            return {'tipo': 'tabla_cabida'}
    
    # Detectar búsqueda de resoluciones
    if any(palabra in entrada_lower for palabra in ['resolución', 'resoluciones']):
        return {'tipo': 'resoluciones'}
    
    # Detectar número de tomo específico
    import re
    tomo_match = re.search(r'tomo\s+(\d+)', entrada_lower)
    if tomo_match:
        return {'tipo': 'tomo_especifico', 'tomo': int(tomo_match.group(1))}
    
    return None

def procesar_consulta_especifica(entrada, tipo_consulta):
    """Procesa consultas específicas sobre recursos estructurados"""
    entrada_lower = entrada.lower()
    
    # Extraer número de tomo si se menciona
    import re
    tomo_match = re.search(r'tomo\s+(\d+)', entrada_lower)
    tomo = int(tomo_match.group(1)) if tomo_match else None
    
    if tipo_consulta['tipo'] == 'indice_completo':
        return generar_indice_completo()
    
    elif tipo_consulta['tipo'] == 'flujograma':
        resultados = buscar_flujograma(tipo_consulta['subtipo'], tomo)
        if resultados:
            respuesta = f"🔄 **Flujograma - {tipo_consulta['subtipo'].title()}:**\n\n"
            for resultado in resultados:
                respuesta += f"{resultado}\n\n"
            respuesta += "---\n💡 *Información extraída de los archivos de flujogramas por tomo*"
            return respuesta
    
    elif tipo_consulta['tipo'] == 'tabla_cabida':
        resultados = buscar_tabla_cabida(tomo)
        if resultados:
            respuesta = "📊 **Tabla de Cabida - Distritos de Calificación:**\n\n"
            for resultado in resultados:
                respuesta += f"{resultado}\n\n"
            respuesta += "---\n💡 *Información extraída de las tablas de cabida por tomo*"
            return respuesta
    
    elif tipo_consulta['tipo'] == 'resoluciones':
        # Detectar tema específico
        tema = None
        if 'ambiente' in entrada_lower or 'ambiental' in entrada_lower:
            tema = 'ambiente'
        elif 'construcción' in entrada_lower or 'construccion' in entrada_lower:
            tema = 'construcción'
        elif 'zonificación' in entrada_lower or 'zonificacion' in entrada_lower:
            tema = 'zonificación'
        
        resultados = buscar_resoluciones(tomo, tema)
        if resultados:
            respuesta = "📋 **Resoluciones de la Junta de Planificación:**\n\n"
            for resultado in resultados:
                respuesta += f"{resultado}\n\n"
            respuesta += "---\n💡 *Información extraída de las resoluciones organizadas por tomo*"
            return respuesta
    
    return None

def detectar_tipo_pregunta(entrada):
    """Detecta el tipo de pregunta y determina la mejor estrategia de búsqueda"""
    entrada_lower = entrada.lower()
    
    # Preguntas de comparación/diferencia
    if any(palabra in entrada_lower for palabra in ['diferencia', 'diferencias', 'comparar', 'comparación']):
        return 'comparacion'
    
    # Preguntas sobre el glosario/definiciones (expandido)
    palabras_glosario = ['qué es', 'que es', 'define', 'definición', 'definicion', 'significado', 'explica', 'explícame', 'explicame', 'concepto', 'término', 'termino', 'significa']
    if any(palabra in entrada_lower for palabra in palabras_glosario):
        return 'glosario'

    # Preguntas sobre permisos
    if any(palabra in entrada_lower for palabra in ['permiso', 'autorización', 'licencia', 'trámite']):
        return 'permisos'

    # Preguntas sobre construcción
    if any(palabra in entrada_lower for palabra in ['construcción', 'edificar', 'estructura', 'obra']):
        return 'construccion'

    # Preguntas sobre planificación
    if any(palabra in entrada_lower for palabra in ['plan', 'zonificación', 'ordenación', 'uso de suelo']):
        return 'planificacion'

    # Preguntas ambientales
    if any(palabra in entrada_lower for palabra in ['ambiental', 'conservación', 'aguas', 'desperdicios']):
        return 'ambiental'

    return 'general'
    if any(palabra in entrada_lower for palabra in ['permiso', 'autorización', 'licencia', 'trámite']):
        return 'permisos'

    # Preguntas sobre construcción
    if any(palabra in entrada_lower for palabra in ['construcción', 'edificar', 'estructura', 'obra']):
        return 'construccion'

    # Preguntas sobre planificación
    if any(palabra in entrada_lower for palabra in ['plan', 'zonificación', 'ordenación', 'uso de suelo']):
        return 'planificacion'

    # Preguntas ambientales
    if any(palabra in entrada_lower for palabra in ['ambiental', 'conservación', 'aguas', 'desperdicios']):
        return 'ambiental'

    return 'general'


def es_pregunta_simple(entrada):
    """Determina si una pregunta es simple y puede responderse con información limitada"""
    entrada_lower = entrada.lower()
    
    # Preguntas que requieren búsqueda específica
    palabras_complejas = [
        "todos", "lista", "cantidad", "cuantos", "cuántos", "comparar", "diferencia",
        "análisis", "resumen", "procedimiento completo", "proceso completo"
    ]
    
    # Preguntas simples típicas
    palabras_simples = [
        "qué es", "que es", "define", "definición", "significa", 
        "cómo se", "como se", "para qué", "para que"
    ]
    
    # Si tiene palabras complejas, no es simple
    if any(palabra in entrada_lower for palabra in palabras_complejas):
        return False
    
    # Si tiene palabras simples o es muy corta, es simple
    if any(palabra in entrada_lower for palabra in palabras_simples):
        return True
    
    # Si la pregunta es muy corta (menos de 5 palabras), probablemente es simple
    return len(entrada.split()) <= 5

def evaluar_relevancia_tomo(entrada, archivo_tomo):
    """Evalúa qué tan relevante es un tomo para una pregunta específica"""
    try:
        with open(archivo_tomo, 'r', encoding='utf-8') as f:
            contenido = f.read().lower()
        
        palabras_pregunta = [palabra.lower() for palabra in entrada.split() if len(palabra) > 3]
        score_relevancia = 0
        
        for palabra in palabras_pregunta:
            if palabra in contenido:
                # Contar ocurrencias pero dar más peso a palabras menos comunes
                ocurrencias = contenido.count(palabra)
                if ocurrencias > 0:
                    # Palabras menos frecuentes tienen más peso
                    peso = min(5, 10 // max(1, ocurrencias // 10))
                    score_relevancia += ocurrencias * peso
        
        return score_relevancia
    except:
        return 0


def procesar_pregunta_legal(entrada):
    """Procesa preguntas legales buscando en los tomos y recursos especializados"""
    entrada_lower = entrada.lower()
    
    # Detectar preguntas sobre títulos de tomos
    palabras_titulos = ["titulo", "títulos", "titulos", "nombre", "nombres", "llamar", "llama", "indices", "indice", "índice", "índices"]
    palabras_tomos = ["tomo", "tomos", "11 tomos", "once tomos", "todos los tomos", "cada tomo"]
    
    busca_titulos = any(palabra in entrada_lower for palabra in palabras_titulos) and any(palabra in entrada_lower for palabra in palabras_tomos)
    busca_listado = any(palabra in entrada_lower for palabra in ["dame", "dime", "muestra", "muéstra", "lista", "listado", "cuales", "cuáles"])
    
    # Si pregunta específicamente por títulos o índice de tomos
    if busca_titulos or (busca_listado and any(palabra in entrada_lower for palabra in palabras_tomos)):
        return obtener_titulos_tomos()
    
    # Palabras que indican análisis complejo
    palabras_analisis = ["resumen", "comparar", "diferencia", "análisis", "explicar", "procedimiento", 
                        "proceso", "pasos", "cómo", "cuándo", "dónde", "requisitos", "lista", "todos los",
                        "cuantas", "cuántas", "cantidad", "número", "listame", "listame"]
    
    # Palabras que indican búsqueda de recursos especializados
    palabras_flujograma = ["flujograma", "flujo", "diagrama", "pasos", "procedimiento", "proceso", 
                          "cambios de calificacion", "sitios historicos", "terrenos publicos"]
    palabras_tabla = ["tabla", "cabida", "distritos", "calificacion"]
    palabras_resolucion = ["resolucion", "resoluciones", "junta de planificacion"]
    
    requiere_analisis = any(palabra in entrada_lower for palabra in palabras_analisis)
    buscar_flujograma = any(palabra in entrada_lower for palabra in palabras_flujograma)
    buscar_tabla = any(palabra in entrada_lower for palabra in palabras_tabla)
    buscar_resolucion = any(palabra in entrada_lower for palabra in palabras_resolucion)
    
    # Detectar si se menciona un tomo específico
    tomo_detectado = re.search(r'tomo\s*(\d+)', entrada.lower())
    rutas_por_probar = []
    recursos_especializados = []

    if tomo_detectado:
        numero = tomo_detectado.group(1)
        rutas_por_probar.append((numero, os.path.join("data", f"tomo_{numero}.txt")))
        
        # Buscar recursos especializados del tomo específico
        base_path = os.path.join("data", "RespuestasParaChatBot", f"RespuestasIA_Tomo{numero}")
        
        if buscar_flujograma:
            flujogramas_path = os.path.join(base_path, "Flujogramas")
            if os.path.exists(flujogramas_path):
                for archivo in os.listdir(flujogramas_path):
                    if archivo.endswith('.txt'):
                        recursos_especializados.append(("Flujograma", os.path.join(flujogramas_path, archivo)))
            # También buscar flujogramas en el directorio principal del tomo
            for archivo in ["flujogramaCambiosCalificacion_Tomo_{}.txt".format(numero),
                           "flujogramaSitiosHistoricos_Tomo_{}.txt".format(numero),
                           "flujogramaTerrPublicos_Tomo_{}.txt".format(numero)]:
                ruta_archivo = os.path.join(base_path, archivo)
                if os.path.exists(ruta_archivo):
                    recursos_especializados.append(("Flujograma", ruta_archivo))
        
        if buscar_tabla:
            tabla_path = os.path.join(base_path, f"TablaCabida_Tomo_{numero}.txt")
            if os.path.exists(tabla_path):
                recursos_especializados.append(("Tabla", tabla_path))
        
        if buscar_resolucion:
            resolucion_path = os.path.join(base_path, f"Resoluciones_Tomo_{numero}.txt")
            if os.path.exists(resolucion_path):
                recursos_especializados.append(("Resolución", resolucion_path))
    else:
        # Para preguntas generales, evaluar relevancia de cada tomo primero
        relevancia_tomos = []
        
        for i in range(1, 12):
            ruta = os.path.join("data", f"tomo_{i}.txt")
            if os.path.exists(ruta):
                score = evaluar_relevancia_tomo(entrada, ruta)
                if score > 0:  # Solo incluir tomos con alguna relevancia
                    relevancia_tomos.append((score, i, ruta))
        
        # Ordenar por relevancia y tomar los más relevantes
        relevancia_tomos.sort(key=lambda x: x[0], reverse=True)
        
        # Para preguntas simples, limitar a 1 tomo más relevante
        # Para preguntas complejas, usar hasta 3 tomos
        es_simple = es_pregunta_simple(entrada)
        max_tomos = 1 if es_simple else (2 if len(entrada.split()) <= 8 else 3)
        
        # Solo usar tomos con score significativo
        umbral_relevancia = 3 if es_simple else 5
        tomos_relevantes = [tomo for tomo in relevancia_tomos if tomo[0] >= umbral_relevancia]
        
        if not tomos_relevantes:
            # Si no hay tomos muy relevantes, usar el más relevante disponible
            tomos_relevantes = relevancia_tomos[:1]
        
        for score, tomo_id, ruta in tomos_relevantes[:max_tomos]:
            rutas_por_probar.append((tomo_id, ruta))
            
        # Si solicita recursos especializados, buscar solo en tomos relevantes
        if buscar_flujograma or buscar_tabla or buscar_resolucion:
            for score, i, _ in tomos_relevantes[:max_tomos]:
                base_path = os.path.join("data", "RespuestasParaChatBot", f"RespuestasIA_Tomo{i}")
                
                if buscar_flujograma:
                    # Buscar en directorio Flujogramas
                    flujogramas_path = os.path.join(base_path, "Flujogramas")
                    if os.path.exists(flujogramas_path):
                        for archivo in os.listdir(flujogramas_path):
                            if archivo.endswith('.txt'):
                                recursos_especializados.append(("Flujograma", os.path.join(flujogramas_path, archivo)))
                    
                    # Buscar en directorio principal del tomo
                    for archivo in ["flujogramaCambiosCalificacion_Tomo_{}.txt".format(i),
                                   "flujogramaSitiosHistoricos_Tomo_{}.txt".format(i),
                                   "flujogramaTerrPublicos_Tomo_{}.txt".format(i)]:
                        ruta_archivo = os.path.join(base_path, archivo)
                        if os.path.exists(ruta_archivo):
                            recursos_especializados.append(("Flujograma", ruta_archivo))

    respuestas_acumuladas = []

    # Procesar recursos especializados PRIMERO (flujogramas, tablas, resoluciones)
    for tipo_recurso, ruta_recurso in recursos_especializados:
        try:
            with open(ruta_recurso, "r", encoding="utf-8") as f:
                contenido_recurso = f.read()

            prompt_especializado = f"""Eres Agente de planificación, un asistente legal especializado en las leyes de planificación de Puerto Rico.

{tipo_recurso.upper()} ESPECIALIZADO:
{contenido_recurso}

PREGUNTA DEL USUARIO: {entrada}

INSTRUCCIONES:
1. Este es un {tipo_recurso.lower()} oficial del sistema legal de Puerto Rico
2. Presenta la información de forma clara y estructurada
3. Si es un flujograma, explica los pasos secuencialmente
4. Si es una tabla, presenta los datos organizadamente
5. Mantén el formato visual con emojis y estructuras claras

RESPUESTA ESPECIALIZADA:"""
            
            mensajes_especializado = [
                {"role": "system", "content": f"Eres Agente de planificación, experto en presentar {tipo_recurso.lower()}s legales de forma clara y estructurada."},
                {"role": "user", "content": prompt_especializado}
            ]

            respuesta = client.chat.completions.create(
                model="gpt-4o",
                messages=mensajes_especializado,
                temperature=0.1
            )
            contenido = respuesta.choices[0].message.content.strip()

            if contenido and len(contenido) > 50:
                nombre_archivo = os.path.basename(ruta_recurso)
                respuestas_acumuladas.append(f"\n📋 **{tipo_recurso} Especializado - {nombre_archivo}**:\n{contenido}")

        except Exception as e:
            continue

    for tomo_id, ruta in rutas_por_probar:
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                contexto_legal = f.read()

            # Mejorar la estrategia de fragmentación para preservar información completa
            max_chars = 6000 if requiere_analisis else 4000  # Aumentar tamaño para más contexto
            
            if len(contexto_legal) > max_chars:
                # Buscar secciones específicas primero
                palabras_pregunta = entrada.lower().split()
                
                # Identificar secciones relevantes por palabras clave
                secciones_relevantes = []
                lineas = contexto_legal.split('\n')
                
                for i, linea in enumerate(lineas):
                    linea_lower = linea.lower()
                    relevancia_linea = 0
                    
                    # Buscar coincidencias exactas en títulos/secciones
                    for palabra in palabras_pregunta:
                        if len(palabra) > 2 and palabra in linea_lower:
                            relevancia_linea += 3
                    
                    # Palabras clave importantes para estructura
                    palabras_clave = ["cantidad", "lista", "catálogo", "licencias", "certificaciones", 
                                     "requisitos", "procedimiento", "proceso", "pasos", "resumen"]
                    for palabra in palabras_clave:
                        if palabra in linea_lower:
                            relevancia_linea += 2
                    
                    if relevancia_linea > 0:
                        # Incluir contexto alrededor de la línea relevante
                        inicio = max(0, i - 5)
                        fin = min(len(lineas), i + 20)  # Más líneas después para capturar listas
                        seccion = '\n'.join(lineas[inicio:fin])
                        secciones_relevantes.append((relevancia_linea, seccion))
                
                if secciones_relevantes:
                    # Ordenar por relevancia y tomar las mejores secciones
                    secciones_relevantes.sort(key=lambda x: x[0], reverse=True)
                    contexto_legal = '\n\n'.join([seccion[1] for seccion in secciones_relevantes[:3]])
                else:
                    # Si no encuentra secciones específicas, usar fragmentación normal pero mejorada
                    overlap = 500
                    fragmentos = []
                    for i in range(0, len(contexto_legal), max_chars - overlap):
                        fragmento = contexto_legal[i:i + max_chars]
                        fragmentos.append(fragmento)
                    
                    # Buscar el fragmento más relevante
                    mejor_fragmento = fragmentos[0]
                    max_relevancia = 0
                    
                    for fragmento in fragmentos:
                        fragmento_lower = fragmento.lower()
                        relevancia = 0
                        
                        for palabra in palabras_pregunta:
                            if len(palabra) > 2:
                                relevancia += fragmento_lower.count(palabra) * 3
                        
                        if relevancia > max_relevancia:
                            max_relevancia = relevancia
                            mejor_fragmento = fragmento
                    
                    contexto_legal = mejor_fragmento
            
            # Prompt mejorado y más específico
            prompt = f"""Eres Agente de planificación, un asistente legal especializado en las leyes de planificación de Puerto Rico.

CONTEXTO LEGAL COMPLETO DEL TOMO {tomo_id}:
{contexto_legal}

PREGUNTA DEL USUARIO: {entrada}

INSTRUCCIONES CRÍTICAS:
1. Analiza TODO el contexto legal proporcionado
2. La información ESTÁ en el texto - tu trabajo es encontrarla y presentarla
3. Si se pregunta por cantidades, listas o números, CUENTA y LISTA TODO lo que encuentres
4. NO digas "no encontrado" - la información existe, búscala cuidadosamente
5. Proporciona respuestas COMPLETAS y DETALLADAS
6. Si es una lista, enumera TODOS los elementos
7. Si es una cantidad, da el número exacto y la lista completa
8. Mantén un tono profesional pero claro

RESPUESTA COMPLETA Y DETALLADA:"""
            
            mensajes_temp = [
                {"role": "system", "content": "Eres Agente de planificación, un asistente legal experto que SIEMPRE encuentra la información en el texto proporcionado. Tu trabajo es analizar completamente el contexto y proporcionar respuestas exactas y completas. La información SIEMPRE está disponible en el texto."},
                {"role": "user", "content": prompt}
            ]

            respuesta = client.chat.completions.create(
                model="gpt-4o",
                messages=mensajes_temp,
                temperature=0.1  # Reducir creatividad para más precisión
            )
            contenido = respuesta.choices[0].message.content.strip()

            # Ser menos restrictivo - solo excluir respuestas claramente vacías
            if contenido and len(contenido) > 50:  # Si hay contenido sustancial
                respuestas_acumuladas.append(f"\n📘 **Respuesta basada en Tomo {tomo_id}**:\n{contenido}")

        except FileNotFoundError:
            continue
        except Exception as e:
            continue

    if respuestas_acumuladas:
        respuesta_final = "\n".join(respuestas_acumuladas)
        
        # Agregar información sobre la búsqueda si fue limitada
        if not tomo_detectado and len(rutas_por_probar) < 3:
            tomos_buscados = [str(tomo_id) for tomo_id, _ in rutas_por_probar]
            respuesta_final += f"\n\n💡 *Búsqueda optimizada en {len(rutas_por_probar)} tomo(s) más relevante(s): {', '.join(tomos_buscados)}. Para una búsqueda más amplia, especifica un tomo o haz una pregunta más específica.*"
        
        return respuesta_final
    else:
        return "Permíteme revisar nuevamente los documentos legales para encontrar esa información específica. Por favor, intenta reformular tu pregunta de manera más específica o indica un tomo particular si conoces dónde puede estar la información."

@app.route('/')
def index():
    """Página principal con verificación de beta"""
    from datetime import datetime
    
    # Verificar si la beta está activa
    beta_activa, dias_restantes = verificar_beta_activa()
    
    if not beta_activa:
        # Si la beta expiró, mostrar página de expiración
        return render_template('beta_expirada.html', 
                             fecha_expiracion=formatear_fecha_espanol(FECHA_EXPIRACION_BETA))
    
    # Si está activa, mostrar la aplicación con info de beta
    current_time = datetime.now().strftime('%H:%M')
    return render_template('index_v2.html', 
                         current_time=current_time,
                         es_beta=True,
                         dias_restantes=dias_restantes,
                         fecha_expiracion=formatear_fecha_espanol(FECHA_EXPIRACION_BETA))

@app.route('/v2')
def index_v2():
    """Página principal V2 - Nueva interfaz (también con beta)"""
    from datetime import datetime
    
    # Verificar si la beta está activa
    beta_activa, dias_restantes = verificar_beta_activa()
    
    if not beta_activa:
        return render_template('beta_expirada.html', 
                             fecha_expiracion=formatear_fecha_espanol(FECHA_EXPIRACION_BETA))
    
    current_time = datetime.now().strftime('%H:%M')
    return render_template('index_v2.html', 
                         current_time=current_time,
                         es_beta=True,
                         dias_restantes=dias_restantes,
                         fecha_expiracion=formatear_fecha_espanol(FECHA_EXPIRACION_BETA))

@app.route('/test')
def test():
    """Página de prueba para CSS"""
    return render_template('test.html')

@app.route('/debug')
def debug():
    """Página de debug para verificar Flask"""
    return """
    <h1>Flask Debug Page</h1>
    <p>Si ves esta página, Flask está funcionando correctamente.</p>
    <p><a href="/">Ir a la página principal</a></p>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        h1 { color: green; }
    </style>
    """

@app.route('/static/<path:filename>')
def custom_static(filename):
    """Servir archivos estáticos con headers específicos para evitar cache"""
    response = send_from_directory('static', filename)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint para procesar mensajes del chat con verificación de beta"""
    try:
        # Verificar si la beta está activa antes de procesar el chat
        beta_activa, _ = verificar_beta_activa()
        if not beta_activa:
            return jsonify({
                'error': 'La versión beta ha expirado',
                'message': f'Esta versión beta expiró el {formatear_fecha_espanol(FECHA_EXPIRACION_BETA)}. Contacta al administrador para obtener la versión completa.'
            }), 403
        data = request.get_json()
        mensaje = data.get('message', '').strip()
        
        if not mensaje:
            return jsonify({'error': 'Mensaje vacío'}), 400
        
        conversation_id = get_conversation_id()
        inicializar_conversacion(conversation_id)
        
        # Detección de preguntas legales
        entrada_lower = mensaje.lower()
        
        # Respuestas sobre estructura del documento
        if "cuantos tomos" in entrada_lower or "cuántos tomos" in entrada_lower:
            respuesta = "📚 Este documento está compuesto por **11 tomos** en total (Tomo 1 al Tomo 11), que contienen las regulaciones completas de planificación de Puerto Rico. Cada tomo cubre diferentes aspectos de la legislación.\n\n**Además, tengo acceso a un Glosario completo (Tomo 12)** con definiciones de términos legales específicos."
            return jsonify({
                'response': respuesta,
                'type': 'info'
            })
        
        # Detectar tipo de pregunta
        tipo_pregunta = detectar_tipo_pregunta(mensaje)
        
        # Detectar si es pregunta legal (MOVER AL INICIO)
        es_legal = any(palabra.lower() in entrada_lower for palabra in palabras_legales)
        if not es_legal and "tomo" in entrada_lower:
            es_legal = True
        
        # Primero: Verificar si es una consulta específica sobre recursos estructurados
        consulta_especifica = detectar_consulta_especifica(mensaje)
        if consulta_especifica:
            respuesta_especifica = procesar_consulta_especifica(mensaje, consulta_especifica)
            if respuesta_especifica:
                return jsonify({
                    'response': respuesta_especifica,
                    'type': 'recurso_especifico'
                })
        
        # Segundo: SIEMPRE intentar buscar en el glosario PRIMERO para cualquier pregunta legal
        respuesta_glosario = None
        if es_legal or tipo_pregunta in ['glosario', 'comparacion', 'permisos', 'construccion', 'planificacion', 'ambiental']:
            respuesta_glosario = procesar_pregunta_glosario(mensaje)
        
        # Manejar preguntas comparativas
        if tipo_pregunta == 'comparacion' and respuesta_glosario:
            return jsonify({
                'response': respuesta_glosario,
                'type': 'comparacion'
            })
        
        # Si es una pregunta de definición y encontramos algo en el glosario, devolverlo
        if tipo_pregunta == 'glosario' and respuesta_glosario:
            return jsonify({
                'response': respuesta_glosario,
                'type': 'glosario'
            })
        
        # Agregar contexto del glosario a preguntas legales relevantes
        contexto_glosario = ""
        if tipo_pregunta in ['permisos', 'construccion', 'planificacion', 'ambiental']:
            # Buscar términos relevantes en el glosario
            palabras_clave = mensaje.lower().split()
            for palabra in palabras_clave:
                if len(palabra) > 3:
                    definiciones = buscar_en_glosario(palabra)
                    if definiciones and len(definiciones) <= 2:  # Limitar para no sobrecargar
                        contexto_glosario += f"\n\n**Definiciones relevantes del glosario:**\n"
                        for def_encontrada in definiciones[:2]:  # Máximo 2 definiciones
                            contexto_glosario += f"{def_encontrada}\n"
                        break
        
        if es_legal:
            respuesta = procesar_pregunta_legal(mensaje)
            
            # Si tenemos respuesta del glosario, combinarla con la respuesta legal
            if respuesta_glosario and respuesta_glosario not in respuesta:
                respuesta = f"{respuesta_glosario}\n\n---\n\n{respuesta}"
            
            tipo_respuesta = f'legal-{tipo_pregunta}'
        else:
            # Pregunta general
            mensajes_conversacion = conversaciones[conversation_id]
            mensajes_conversacion.append({"role": "user", "content": mensaje})
            
            respuesta_openai = client.chat.completions.create(
                model="gpt-4o",
                messages=mensajes_conversacion
            )
            respuesta = respuesta_openai.choices[0].message.content.strip()
            mensajes_conversacion.append({"role": "assistant", "content": respuesta})
            tipo_respuesta = 'general'
        
        # Guardar en log
        with open("log.txt", "a", encoding="utf-8") as log:
            log.write(f"Pregunta: {mensaje}\nRespuesta: {respuesta}\n---\n")
        
        return jsonify({
            'response': respuesta,
            'type': tipo_respuesta
        })
        
    except Exception as e:
        print(f"Error en chat: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/nueva-conversacion', methods=['POST'])
def nueva_conversacion():
    """Endpoint para iniciar una nueva conversación"""
    if 'conversation_id' in session:
        del session['conversation_id']
    return jsonify({'success': True})

@app.route('/health')
def health():
    """Endpoint de salud para verificar que la aplicación está funcionando"""
    return jsonify({'status': 'ok', 'service': 'Agente de planificación Web'})

@app.route('/favicon.ico')
def favicon():
    """Servir favicon"""
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    import webbrowser
    import threading
    import time
    
    # Función para abrir el navegador después de un pequeño delay
    def open_browser():
        time.sleep(1.5)  # Esperar a que el servidor esté listo
        webbrowser.open('http://127.0.0.1:5001')
    
    # Crear carpeta de templates si no existe
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Abrir navegador en un hilo separado
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Ejecutar con menos debug info para el ejecutable
    debug_mode = not getattr(sys, 'frozen', False)  # False si es ejecutable
    app.run(debug=debug_mode, host='0.0.0.0', port=5001)
