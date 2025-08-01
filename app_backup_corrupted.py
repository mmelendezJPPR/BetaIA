from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_cors import CORS
import os
import re
import sys
import uuid
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
import hashlib

# CONFIGURACIÓN BETA - FECHA DE EXPIRACIÓN
# Beta profesional por días para demostración oficial
FECHA_EXPIRACION_BETA = datetime(2025, 8, 2)  # 2 de agosto 2025 - 5 días para demostración completa

def formatear_fecha_espanol(fecha):
    """Convierte una fecha al formato español"""
    meses_e        return f"""
📚 **Reglamento de Emergencia JP-RP-41 (ACTUALIZADO)**

Este sistema utiliza exclusivamente el **Reglamento de Emergencia JP-RP-41**, la regulación más actualizada para planificación en Puerto Rico.ol = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }

    if isinstance(fecha, datetime):
        dia = fecha.day
        mes = meses_espanol[fecha.month]
        año = fecha.year
        return f"{dia} de {mes} de {año}"
    else:
        dia = fecha.day
        mes = meses_espanol[fecha.month]
        año = fecha.year
        return f"{dia} de {mes} de {año}"
    

def verificar_beta_activa():
    """Verifica si la versión beta sigue activa"""
    ahora = datetime.now()
    
    if ahora <= FECHA_EXPIRACION_BETA:
        tiempo_restante = FECHA_EXPIRACION_BETA - ahora
        dias_restantes = tiempo_restante.days
        horas_restantes = int(tiempo_restante.total_seconds() // 3600) % 24
        
        # Retornar días si quedan más de 1 día, horas si queda menos de 1 día
        if dias_restantes > 0:
            return True, f"{dias_restantes} días"
        else:
            return True, f"{horas_restantes} horas"
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

# Función para obtener información sobre el reglamento de emergencia
def obtener_info_reglamento_emergencia():
    """Devuelve información sobre el Reglamento de Emergencia JP-RP-41"""
    if reglamento_emergencia:
        return f"""
**📋 REGLAMENTO DE EMERGENCIA JP-RP-41**

Este sistema utiliza exclusivamente el **Reglamento de Emergencia JP-RP-41**, la regulación más actualizada para planificación en Puerto Rico.

**Características del reglamento:**
- Documento completo y actualizado: {len(reglamento_emergencia):,} caracteres
- Cobertura: Todas las disposiciones de planificación y desarrollo
- Estado: Vigente y operativo para todas las consultas legales

**Capacidades de búsqueda:**
✅ Búsqueda inteligente por temas específicos
✅ Análisis contextual de regulaciones
✅ Interpretación de procedimientos y requisitos
✅ Consultas sobre permisos y certificaciones
✅ Información sobre zonificación y uso de suelo

💡 **Nota importante:** Toda la información legal proviene exclusivamente del Reglamento de Emergencia JP-RP-41. Este sistema no utiliza el Reglamento Conjunto 2020 u otras regulaciones anteriores.
"""
    else:
        return """
⚠️ **REGLAMENTO DE EMERGENCIA JP-RP-41 NO DISPONIBLE**

El reglamento de emergencia no está cargado en el sistema.
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
- Proporciona respuestas completas y detalladas basadas ÚNICAMENTE en el Reglamento de Emergencia JP-RP-41
- Explica conceptos legales de manera clara
- Siempre usa SOLO la información del Reglamento de Emergencia JP-RP-41
- Mantén un tono profesional pero accesible
- Recomienda al usuario cómo hacer preguntas más específicas si es necesario
- Enumera los terminos repetidos en el reglamento de emergencia y mencionalos
- Las respuestas no puede contender palabras repetidas, si es necesario, usa sinónimos o reformula la respuesta

FUENTE DE INFORMACIÓN:
- ÚNICAMENTE el Reglamento de Emergencia JP-RP-41
- Glosario de términos especializados (como apoyo)

IMPORTANTE:
- NO uses información del Reglamento Conjunto 2020
- NO menciones "tomos" específicos del reglamento anterior  
- TODA la información legal debe provenir del Reglamento de Emergencia JP-RP-41
- Si no tienes información específica en el reglamento de emergencia, indícalo claramente

CAPACIDADES:
- Búsqueda inteligente en el Reglamento de Emergencia JP-RP-41
- Análisis de regulaciones y procedimientos de planificación
- Explicación de requisitos para permisos y certificaciones
- Consultas sobre zonificación y desarrollo urbano
- Definiciones del glosario especializado
- Tomo 11: Querellas
- Glosario de términos especializados (Tomo 12) - COMPLETAMENTE DISPONIBLE
- 🚨 Reglamento de Emergencia JP-RP-41 (ACTUALIZADO) - DISPONIBLE

GLOSARIO DISPONIBLE:
"""}
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

# Añadir al inicio del archivo con las otras cargas
def cargar_reglamento_emergencia():
    """Carga el reglamento de emergencia JP-RP-41"""
    ruta_emergencia = os.path.join("data", "reglamento_emergencia_jp41_chatbot_20250731_155845.json")
    if os.path.exists(ruta_emergencia):
        try:
            with open(ruta_emergencia, "r", encoding="utf-8") as f:
                data = json.load(f)
            contenido = data.get('analisis_completo', '')
            print(f"✅ Reglamento de Emergencia JP-RP-41 cargado: {len(contenido)} caracteres")
            return contenido
        except Exception as e:
            print(f"❌ Error cargando reglamento emergencia: {e}")
            return ""
    else:
        print(f"❌ Archivo no encontrado: {ruta_emergencia}")
        return ""

# Sistema de caché para respuestas frecuentes
import hashlib
cache_respuestas = {}

reglamento_emergencia = cargar_reglamento_emergencia()

def buscar_en_reglamento_emergencia(entrada):
    """Busca información específica en el reglamento de emergencia JP-RP-41 - VERSIÓN OPTIMIZADA"""
    if not reglamento_emergencia:
        return None
    
    # Verificar caché primero
    cache_key = hashlib.md5(entrada.lower().encode()).hexdigest()
    if cache_key in cache_respuestas:
        return cache_respuestas[cache_key]
    
    try:
        # Fragmentar el reglamento en chunks más inteligentes
        max_chars = 12000  # Aumentar para mejor contexto
        
        if len(reglamento_emergencia) > max_chars:
            # Algoritmo de búsqueda mejorado
            palabras_pregunta = [p.lower() for p in entrada.split() if len(p) > 3]
            lineas = reglamento_emergencia.split('\n')
            
            # Crear índice de relevancia más sofisticado
            secciones_relevantes = []
            for i, linea in enumerate(lineas):
                linea_lower = linea.lower()
                relevancia = 0
                
                # Puntaje por coincidencias exactas
                for palabra in palabras_pregunta:
                    coincidencias = linea_lower.count(palabra)
                    relevancia += coincidencias * 5
                
                # Puntaje adicional para términos legales clave
                terminos_legales = ['artículo', 'sección', 'permiso', 'certificación', 'procedimiento', 'requisito']
                for termino in terminos_legales:
                    if termino in linea_lower:
                        relevancia += 2
                
                if relevancia > 0:
                    # Capturar más contexto para mejor comprensión
                    inicio = max(0, i - 15)
                    fin = min(len(lineas), i + 40)
                    seccion = '\n'.join(lineas[inicio:fin])
                    secciones_relevantes.append((relevancia, seccion, i))
            
            if secciones_relevantes:
                # Ordenar por relevancia y eliminar duplicados
                secciones_relevantes.sort(key=lambda x: x[0], reverse=True)
                secciones_unicas = []
                lineas_usadas = set()
                
                for relevancia, seccion, linea_num in secciones_relevantes:
                    if linea_num not in lineas_usadas:
                        secciones_unicas.append(seccion)
                        lineas_usadas.update(range(max(0, linea_num-15), min(len(lineas), linea_num+40)))
                        if len(secciones_unicas) >= 3:  # Máximo 3 secciones
                            break
                
                contenido_relevante = '\n\n===SECCIÓN RELEVANTE===\n\n'.join(secciones_unicas)
            else:
                # Estrategia de fallback mejorada
                contenido_relevante = reglamento_emergencia[:max_chars]
        else:
            contenido_relevante = reglamento_emergencia
        
        # Prompt optimizado para mejores respuestas
        prompt = f"""Eres Agente de Planificación, especialista experto en el Reglamento de Emergencia JP-RP-41 de Puerto Rico.

CONTEXTO LEGAL DEL REGLAMENTO JP-RP-41:
{contenido_relevante}

CONSULTA DEL USUARIO: {entrada}

INSTRUCCIONES ESPECÍFICAS:
1. Analiza meticulosamente el contexto legal proporcionado
2. Identifica artículos, secciones o disposiciones específicas relevantes
3. Proporciona una respuesta estructurada y completa
4. Incluye referencias específicas del reglamento cuando sea posible
5. Si hay procedimientos, descríbelos paso a paso
6. Mantén un lenguaje claro pero técnicamente preciso
7. Indica siempre que la información proviene del Reglamento JP-RP-41

FORMATO DE RESPUESTA PREFERIDO:
- Respuesta directa a la consulta
- Referencias específicas del reglamento
- Procedimientos paso a paso (si aplica)
- Consideraciones adicionales importantes

RESPUESTA ESPECIALIZADA:"""
        
        # Usar el cliente OpenAI para procesar la consulta con validación
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Eres Agente de planificación, experto en reglamentos de emergencia de Puerto Rico. Analiza el contenido del reglamento JP-RP-41 y proporciona respuestas precisas y completas. IMPORTANTE: Solo responde basándote en el contenido proporcionado del reglamento."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500  # Limitar para respuestas más concisas
        )
        
        contenido_respuesta = response.choices[0].message.content.strip()
        
        if contenido_respuesta and len(contenido_respuesta) > 50:
            resultado = f"🚨 **REGLAMENTO DE EMERGENCIA JP-RP-41 (ACTUALIZADO)**:\n\n{contenido_respuesta}\n\n---\n💡 *Información extraída del Reglamento de Emergencia JP-RP-41*"
            
            # Guardar en caché para consultas futuras
            cache_respuestas[cache_key] = resultado
            
            return resultado
        
    except Exception as e:
        print(f"Error procesando reglamento de emergencia: {e}")
    
    return None

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
    """Detecta consultas específicas - ahora redirige al procesamiento normal"""
    # Todas las consultas van al procesamiento normal para usar la búsqueda inteligente
    return None

def procesar_consulta_especifica(entrada, tipo_consulta):
    """Procesa consultas específicas usando ÚNICAMENTE el Reglamento de Emergencia JP-RP-41"""
    
    # Todas las consultas ahora se procesan con el Reglamento de Emergencia
    if tipo_consulta['tipo'] in ['indice_completo', 'flujograma', 'tabla_cabida', 'resoluciones', 'tomo_especifico']:
        return f"""
� **Reglamento de Emergencia JP-RP-41 (ACTUALIZADO)**

Este sistema utiliza exclusivamente el **Reglamento de Emergencia JP-RP-41**, la regulación más actualizada para planificación en Puerto Rico.

🚨 **NOTA IMPORTANTE:** El sistema ya no utiliza los tomos del Reglamento Conjunto 2020. Toda la información legal proviene del Reglamento de Emergencia JP-RP-41.

**Para consultas específicas, reformule su pregunta relacionada con:**
- Permisos de emergencia
- Procedimientos de planificación actualizados  
- Zonificación bajo el reglamento de emergencia
- Normativas ambientales de emergencia
- Desarrollo urbano en situaciones de emergencia

---
💡 *Información basada en el Reglamento de Emergencia JP-RP-41*
"""
    
    return None

def detectar_tipo_pregunta(entrada):
    """Detecta el tipo de pregunta y determina la mejor estrategia de búsqueda"""
    entrada_lower = entrada.lower()
    
    # Preguntas de comparación/diferencia
    if any(palabra in entrada_lower for palabra in ['diferencia', 'diferencias', 'comparar', 'comparación']):
        return 'comparacion'
    
    # Preguntas sobre REQUISITOS Y PROCEDIMIENTOS - PRIORIDAD ALTA para Reglamento
    palabras_requisitos = ['requisito', 'requisitos', 'proceso', 'procedimiento', 'pasos', 'como', 'cómo', 'necesito', 'solicitar', 'obtener', 'tramitar', 'aplicar']
    if any(palabra in entrada_lower for palabra in palabras_requisitos):
        return 'requisitos_procedimientos'
    
    # Preguntas sobre el glosario/definiciones SOLO cuando se pregunta explícitamente
    palabras_glosario = ['qué es', 'que es', 'define', 'definición', 'definicion', 'significado', 'explica', 'explícame', 'explicame', 'concepto', 'término', 'termino', 'significa']
    if any(palabra in entrada_lower for palabra in palabras_glosario):
        return 'glosario'

    # Preguntas sobre permisos - PRIORIDAD REGLAMENTO si hay palabras de acción
    if any(palabra in entrada_lower for palabra in ['permiso', 'autorización', 'licencia', 'trámite']):
        # Si incluye palabras de acción, es requisitos/procedimientos
        if any(accion in entrada_lower for accion in ['requisito', 'como', 'cómo', 'proceso', 'solicitar', 'obtener', 'tramitar']):
            return 'requisitos_procedimientos'
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


def procesar_pregunta_legal(entrada):
    """Procesa preguntas legales usando ÚNICAMENTE el Reglamento de Emergencia JP-RP-41"""
    entrada_lower = entrada.lower()
    
    # Detectar preguntas sobre información del reglamento
    palabras_info = ["que documentos", "que tienes", "información", "documentación", "reglamento", "regulación"]
    palabras_listado = ["dame", "dime", "muestra", "muéstra", "lista", "listado", "cuales", "cuáles"]
    
    busca_info = any(palabra in entrada_lower for palabra in palabras_info)
    busca_listado = any(palabra in entrada_lower for palabra in palabras_listado)
    
    # Si pregunta por información general del sistema
    if busca_info or busca_listado:
        return obtener_info_reglamento_emergencia()
    
    # BÚSQUEDA PRINCIPAL: Siempre usar el reglamento de emergencia para todas las consultas legales
    if reglamento_emergencia:
        respuesta_emergencia = buscar_en_reglamento_emergencia(entrada)
        if respuesta_emergencia:
            return respuesta_emergencia
        else:
            return """
🔍 **Búsqueda completada en Reglamento de Emergencia JP-RP-41**

No se encontró información específica para su consulta en el reglamento de emergencia.

**Sugerencias:**
- Reformule su pregunta con términos más específicos
- Consulte sobre permisos, zonificación, procedimientos o normativas específicas
- El sistema busca en el documento completo del Reglamento de Emergencia JP-RP-41

**Temas disponibles:** permisos, licencias, zonificación, construcción, medio ambiente, planificación, desarrollo urbano, etc.
"""
    else:
        return """
⚠️ **Reglamento de Emergencia JP-RP-41 no disponible**

El sistema no puede procesar su consulta porque el reglamento de emergencia no está cargado.
"""

    # BÚSQUEDA EXCLUSIVA EN REGLAMENTO DE EMERGENCIA JP-RP-41
    respuesta_emergencia = buscar_en_reglamento_emergencia(entrada)
    if respuesta_emergencia:
        return respuesta_emergencia
    else:
        return """
📚 **Término relacionado encontrado en el Glosario**

Se revisó el Reglamento de Emergencia JP-RP-41 y el glosario de términos especializados para responder a su consulta.

🚨 **REGLAMENTO DE EMERGENCIA JP-RP-41 (ACTUALIZADO)**:

Su consulta ha sido procesada exclusivamente usando el Reglamento de Emergencia JP-RP-41. Si necesita información más específica, por favor reformule su pregunta con términos más precisos.

---
💡 *Información extraída del Reglamento de Emergencia JP-RP-41*
"""

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
                         fecha_expiracion=formatear_fecha_espanol(FECHA_EXPIRACION_BETA),
                         fecha_expiracion_iso=FECHA_EXPIRACION_BETA.isoformat())

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
                         fecha_expiracion=formatear_fecha_espanol(FECHA_EXPIRACION_BETA),
                         fecha_expiracion_iso=FECHA_EXPIRACION_BETA.isoformat())

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
        
        # Segundo: Procesar según tipo de pregunta
        respuesta_glosario = None
        
        # Para REQUISITOS/PROCEDIMIENTOS: IR DIRECTO al Reglamento de Emergencia
        if tipo_pregunta == 'requisitos_procedimientos':
            respuesta = procesar_pregunta_legal(mensaje)
            return jsonify({
                'response': respuesta,
                'type': 'requisitos_reglamento'
            })
        
        # Para DEFINICIONES: IR DIRECTO al glosario
        if tipo_pregunta == 'glosario':
            respuesta_glosario = procesar_pregunta_glosario(mensaje)
            if respuesta_glosario:
                return jsonify({
                    'response': respuesta_glosario,
                    'type': 'glosario'
                })
        
        # Para otras preguntas legales: Intentar primero el glosario
        if es_legal or tipo_pregunta in ['permisos', 'construccion', 'planificacion', 'ambiental']:
            respuesta_glosario = procesar_pregunta_glosario(mensaje)
        
        # Manejar preguntas comparativas
        if tipo_pregunta == 'comparacion' and respuesta_glosario:
            return jsonify({
                'response': respuesta_glosario,
                'type': 'comparacion'
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
