"""
ALTERNATIVA INTELIGENTE: Mini-Especialistas
Solo para casos muy específicos que realmente lo necesitan
"""
import re
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class MiniEspecialistaConservacion:
    """Mini especialista SOLO para conservación histórica"""
    
    @staticmethod
    def es_mi_consulta(entrada):
        """Detecta si es específicamente sobre conservación histórica"""
        entrada_lower = entrada.lower()
        
        # Palabras de ALTA PRECISIÓN - solo casos muy específicos
        palabras_especificas = [
            'sitio histórico', 'sitios históricos',
            'designación histórica', 'nominación histórica',
            'conservación histórica', 'patrimonio histórico',
            'icp', 'instituto de cultura',
            'sección 10.1.1', 'criterios históricos'
        ]
        
        return any(palabra in entrada_lower for palabra in palabras_especificas)
    
    @staticmethod
    def procesar(entrada, tomo_10_contenido):
        """Procesamiento ultra-específico para conservación"""
        try:
            prompt_especifico = f"""Eres especialista en conservación histórica de Puerto Rico.

CONSULTA ESPECÍFICA: {entrada}

INFORMACIÓN TOMO 10:
{tomo_10_contenido[:2000]}

INSTRUCCIONES:
- Menciona secciones específicas (10.1.1.1, 10.1.1.2, 10.1.4)
- Explica criterios de elegibilidad
- Incluye procedimientos ICP
- Máximo 400 palabras

RESPUESTA ESPECIALIZADA:"""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Especialista en patrimonio histórico de Puerto Rico."},
                    {"role": "user", "content": prompt_especifico}
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            respuesta = response.choices[0].message.content.strip()
            return f"🏛️ **ESPECIALISTA EN CONSERVACIÓN HISTÓRICA:**\n\n{respuesta}\n\n---\n📜 *Especialista en patrimonio histórico*"
            
        except Exception as e:
            print(f"Error en mini-especialista conservación: {e}")
            return None

class MiniEspecialistaTablas:
    """UN SOLO especialista para TODAS las tablas (cabida, calificaciones, permisos, agencias, menú)"""
    
    @staticmethod
    def es_mi_consulta(entrada):
        """Detecta cualquier solicitud de tabla"""
        entrada_lower = entrada.lower()
        return 'tabla' in entrada_lower
    
    @staticmethod
    def procesar(entrada):
        """Procesa cualquier tipo de tabla según la solicitud"""
        entrada_lower = entrada.lower()
        
        # 1. TABLA DE CABIDA
        if 'cabida' in entrada_lower:
            return MiniEspecialistaTablas._generar_tabla_cabida(entrada)
        
        # 2. TABLA DE CALIFICACIONES
        elif 'calificaciones' in entrada_lower:
            return MiniEspecialistaTablas._generar_tabla_calificaciones()
        
        # 3. TABLA DE PERMISOS
        elif 'permisos' in entrada_lower:
            return MiniEspecialistaTablas._generar_tabla_permisos()
        
        # 4. TABLA DE AGENCIAS
        elif 'agencias' in entrada_lower:
            return MiniEspecialistaTablas._generar_tabla_agencias()
        
        # 5. MENÚ DE OPCIONES (cuando solo dice "tabla" o "generar tabla")
        else:
            return MiniEspecialistaTablas._mostrar_menu_tablas()
    
    @staticmethod
    def _generar_tabla_cabida(entrada):
        """Genera tabla de cabida específica por tomo"""
        tomo = extraer_numero_tomo(entrada)
        
        try:
            tabla_html = None
            
            if tomo:
                # Buscar archivo específico del tomo
                archivo_tomo = f"data/RespuestasParaChatBot/RespuestasIA_Tomo{tomo}/TablaCabida_Tomo_{tomo}.txt"
                try:
                    with open(archivo_tomo, 'r', encoding='utf-8') as f:
                        contenido_tomo = f.read()
                    
                    if contenido_tomo.strip():
                        contenido_limpio = limpiar_contenido_tabla(contenido_tomo)
                        if contenido_limpio:
                            tabla_html = convertir_tabla_a_html(contenido_limpio)
                            titulo = f"📊 TABLA DE CABIDA - TOMO {tomo}"
                    
                except FileNotFoundError:
                    print(f"Archivo específico del Tomo {tomo} no encontrado: {archivo_tomo}")
            
            # Si no se encontró archivo específico, usar tabla genérica
            if not tabla_html:
                tabla_generica = """| Distrito de Calificación | Cabida Mínima | Cabida Máxima | Uso Principal |
|-------------------------|---------------|---------------|---------------|
| Distrito A | 200 m² | 500 m² | Residencial Baja Densidad |
| Distrito B | 150 m² | 400 m² | Residencial Intermedio |
| Distrito C | 100 m² | 300 m² | Residencial Urbano |
| Distrito D | 80 m² | 250 m² | Comercial General |
| Distrito E | 50 m² | 200 m² | Comercial Central |"""
                
                tabla_html = convertir_tabla_a_html(tabla_generica)
                
                if tomo:
                    titulo = f"📊 TABLA DE CABIDA GENÉRICA - TOMO {tomo}"
                    nota = f"<br><em>⚠️ Datos específicos del Tomo {tomo} no disponibles. Mostrando tabla genérica.</em>"
                else:
                    titulo = "📊 TABLA DE CABIDA GENÉRICA"
                    nota = "<br><em>💡 Especifica un tomo (ej: 'tabla de cabida tomo 3')</em>"
            else:
                nota = f"<br><em>✅ Datos específicos del Tomo {tomo}</em>"
            
            respuesta = f"<strong>{titulo}</strong>{tabla_html}{nota}"
            respuesta += "<br>---<br>💡 <i>Tabla procesada por especialista</i>"
            return respuesta
            
        except Exception as e:
            print(f"Error generando tabla cabida: {e}")
            return None
    
    @staticmethod
    def _generar_tabla_calificaciones():
        """Genera tabla de calificaciones zonales"""
        tabla_data = """| Zona de Calificación | Uso Permitido | Densidad Máxima | Altura Máxima |
|---------------------|---------------|-----------------|---------------|
| Zona Residencial R-1 | Residencial Unifamiliar | 1 unidad/solar | 2 pisos |
| Zona Residencial R-2 | Residencial Multifamiliar | 4 unidades/cuerda | 3 pisos |
| Zona Comercial C-1 | Comercio Local | No aplica | 3 pisos |
| Zona Comercial C-2 | Comercio General | No aplica | 5 pisos |
| Zona Industrial I-1 | Industria Liviana | No aplica | 4 pisos |"""
        
        tabla_html = convertir_tabla_a_html(tabla_data)
        respuesta = f"<strong>📊 TABLA DE CALIFICACIONES DE ZONA</strong>{tabla_html}"
        respuesta += "<br>---<br>💡 <i>Tabla generada por especialista</i>"
        return respuesta
    
    @staticmethod
    def _generar_tabla_permisos():
        """Genera tabla de permisos requeridos"""
        tabla_data = """| Tipo de Permiso | Documentos Requeridos | Tiempo de Procesamiento | Costo |
|-----------------|----------------------|------------------------|-------|
| Permiso de Construcción | Planos y Certificaciones | 30-45 días | $500-2000 |
| Permiso de Uso | Solicitud y Certificado | 15-30 días | $100-500 |
| Permiso Ambiental | EIA y Estudios | 60-90 días | $1000-5000 |
| Permiso Comercial | Licencia y Documentos | 20-30 días | $200-800 |
| Permiso Industrial | Planos y Estudios | 45-60 días | $2000-8000 |"""
        
        tabla_html = convertir_tabla_a_html(tabla_data)
        respuesta = f"<strong>📋 TABLA DE PERMISOS REQUERIDOS</strong>{tabla_html}"
        respuesta += "<br>---<br>💡 <i>Tabla generada por especialista</i>"
        return respuesta
    
    @staticmethod
    def _generar_tabla_agencias():
        """Genera tabla de agencias gubernamentales"""
        tabla_data = """| Agencia | Función Principal | Contacto | Horario |
|---------|------------------|----------|---------|
| Junta de Planificación | Planificación Territorial | (787) 723-6200 | 8:00-4:30 |
| DRNA | Recursos Naturales | (787) 999-2200 | 7:30-4:00 |
| ARPE | Permisos | (787) 999-2200 | 8:00-4:30 |
| Municipio | Permisos Locales | Varía | 8:00-4:30 |
| AAA | Agua y Alcantarillado | (787) 620-2270 | 24 horas |"""
        
        tabla_html = convertir_tabla_a_html(tabla_data)
        respuesta = f"<strong>🏢 TABLA DE AGENCIAS RELACIONADAS</strong>{tabla_html}"
        respuesta += "<br>---<br>💡 <i>Tabla generada por especialista</i>"
        return respuesta
    
    @staticmethod
    def _mostrar_menu_tablas():
        """Muestra menú de opciones de tablas disponibles"""
        respuesta = "<strong>🛠️ GENERADOR DE TABLAS DISPONIBLE</strong>"
        respuesta += "<p>Puedo generar las siguientes tablas:</p>"
        
        menu_data = """| Tipo de Tabla | Comando de Ejemplo |
|---------------|-------------------|
| Tabla de Cabida | "tabla de cabida tomo 5" |
| Tabla de Calificaciones | "tabla de calificaciones" |
| Tabla de Permisos | "tabla de permisos" |
| Tabla de Agencias | "tabla de agencias" |"""
        
        tabla_html = convertir_tabla_a_html(menu_data)
        respuesta += tabla_html
        respuesta += "<p><strong>¿Qué tabla te gustaría generar?</strong></p>"
        respuesta += "<br>---<br>💡 <i>Especialista en tablas unificado</i>"
        return respuesta

def limpiar_contenido_tabla(contenido):
    """Limpia el contenido eliminando fragmentos y texto descriptivo, extrae solo la tabla"""
    # Eliminar marcadores de fragmento
    contenido = re.sub(r'🔍\s*[Ff]ragmento\s*\d*\s*:', '', contenido)
    contenido = re.sub(r'[Ff]ragmento\s*\d*\s*:', '', contenido)
    contenido = re.sub(r'FRAGMENTO\s*\d*\s*:', '', contenido)
    
    # Buscar la parte que contiene la tabla (líneas con |)
    lineas = contenido.split('\n')
    lineas_tabla = []
    en_tabla = False
    
    for linea in lineas:
        linea = linea.strip()
        
        # Detectar inicio de tabla
        if '|' in linea and ('Distrito' in linea or 'Cabida' in linea):
            en_tabla = True
        
        # Si estamos en tabla y la línea contiene |, incluirla
        if en_tabla and '|' in linea:
            lineas_tabla.append(linea)
        
        # Detener si encontramos línea vacía después de empezar tabla
        elif en_tabla and linea == '':
            break
        
        # Detener si encontramos texto descriptivo después de tabla
        elif en_tabla and linea and '|' not in linea and len(linea) > 20:
            break
    
    return '\n'.join(lineas_tabla) if lineas_tabla else None

def convertir_tabla_a_html(texto):
    """Convierte texto tabular a HTML - Función mejorada basada en app.py"""
    # Limpiar texto
    texto = texto.strip()
    
    # Eliminar líneas vacías
    lineas = [l.strip() for l in texto.strip().split('\n') if l.strip()]
    
    if not lineas or len(lineas) < 2:
        return f'<pre>{texto}</pre>'
    
    # Detectar tablas Markdown (con | al principio o fin de línea)
    es_markdown = False
    for l in lineas[:3]:
        if l.strip().startswith('|') or l.strip().endswith('|'):
            es_markdown = True
            break
    
    # Limpiar líneas markdown
    if es_markdown:
        lineas_limpias = []
        for l in lineas:
            l = l.strip()
            if l.startswith('|'):
                l = l[1:]
            if l.endswith('|'):
                l = l[:-1]
            # Ignorar líneas separadoras
            if not re.match(r'^[\s\-:|\+]+$', l):
                lineas_limpias.append(l)
        if lineas_limpias:
            lineas = lineas_limpias
    
    # Detectar delimitador
    delimitadores = ['\t', ';', ',', '|']
    delimitador = None
    for d in delimitadores:
        if any(d in l for l in lineas[:3]):
            delimitador = d
            break
    
    if not delimitador:
        return f'<pre>{texto}</pre>'
    
    # Procesar filas
    filas = []
    max_celdas = 0
    
    for linea in lineas:
        celdas = [c.strip() for c in linea.split(delimitador)]
        if not any(c for c in celdas):
            continue
        filas.append(celdas)
        max_celdas = max(max_celdas, len(celdas))
    
    # Normalizar longitud de filas
    for i, fila in enumerate(filas):
        if len(fila) < max_celdas:
            filas[i] = fila + [''] * (max_celdas - len(fila))
    
    if not filas:
        return f'<pre>{texto}</pre>'
    
    # Determinar encabezado y cuerpo
    encabezado = filas[0]
    cuerpo = filas[1:] if len(filas) > 1 else []
    
    # Crear HTML limpio sin espacios extras
    html = '<div class="tabla-container"><table class="tabla-moderna">'
    html += '<thead><tr>' + ''.join(f'<th>{col}</th>' for col in encabezado) + '</tr></thead>'
    html += '<tbody>'
    for fila in cuerpo:
        html += '<tr>' + ''.join(f'<td>{celda}</td>' for celda in fila) + '</tr>'
    html += '</tbody></table></div>'
    
    return html

def procesar_con_mini_especialistas(entrada):
    """
    Función principal que decide si usar mini-especialistas
    SIMPLIFICADO: Solo 2 especialistas
    """
    print(f"🔍 Verificando mini-especialistas para: '{entrada[:50]}...'")
    
    # 1. Verificar conservación histórica
    if MiniEspecialistaConservacion.es_mi_consulta(entrada):
        print("🏛️ Usando mini-especialista: Conservación Histórica")
        
        try:
            with open("data/Tomo_10_Conservacion_Historica.txt", 'r', encoding='utf-8') as f:
                tomo_10_contenido = f.read()
            
            resultado = MiniEspecialistaConservacion.procesar(entrada, tomo_10_contenido)
            if resultado:
                return {
                    'usar_especialista': True,
                    'respuesta': resultado,
                    'tipo': 'mini-especialista-conservacion'
                }
        except Exception as e:
            print(f"Error cargando Tomo 10: {e}")
    
    # 2. Verificar CUALQUIER tabla (unificado)
    if MiniEspecialistaTablas.es_mi_consulta(entrada):
        print("� Usando mini-especialista: Tablas Unificado")
        
        resultado = MiniEspecialistaTablas.procesar(entrada)
        if resultado:
            return {
                'usar_especialista': True,
                'respuesta': resultado,
                'tipo': 'mini-especialista-tablas'
            }
    
    # 3. Si no es caso específico, usar sistema actual
    print("🔄 Usando sistema actual (no requiere especialización)")
    return {
        'usar_especialista': False,
        'mensaje': 'Continuar con sistema actual'
    }

# Función para extraer número de tomo (helper)
def extraer_numero_tomo(texto):
    """Extrae número de tomo del texto"""
    match = re.search(r'tomo\s*(\d+)|del\s+tomo\s*(\d+)', texto.lower())
    if match:
        for grupo in match.groups():
            if grupo is not None:
                return int(grupo)
    return None
