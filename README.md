# 🏛️ Agente de Planificacion - Asistente Legal de Puerto Rico

**Versión Beta** - Asistente especializado en consultas sobre planificación y zonificación de Puerto Rico.

## 📋 Descripción

Agente de planificacion es un asistente de inteligencia artificial especializado en temas legales de planificación y zonificación de Puerto Rico. Proporciona consultas profesionales basadas en la documentación oficial de la Junta de Planificación de Puerto Rico.

## 🚀 Características

- **Interfaz Web Intuitiva**: Diseño profesional con tema navy
- **Sistema Beta**: Versión de prueba con fecha de expiración (15 de agosto, 2025)
- **Base de Conocimientos**: Información actualizada sobre planificación y zonificación
- **Localización**: Completamente en español para Puerto Rico
- **Responsive**: Compatible con dispositivos móviles y desktop

## 🛠️ Tecnologías

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **IA**: OpenAI GPT
- **Deployment**: Railway compatible

## 📦 Instalación

### Requisitos Previos
- Python 3.8+
- API Key de OpenAI

### Pasos de Instalación

1. **Clonar el repositorio**
```bash
git clone [tu-repositorio]
cd ChatBot-AI-main
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno**
```bash
# Crear archivo .env con tu API key
OPENAI_API_KEY=tu_api_key_aqui
```

4. **Ejecutar la aplicación**
```bash
python app.py
```

5. **Acceder a la aplicación**
   - Abrir navegador en: `http://localhost:5001`

## 🌐 Deployment en Railway

1. Conectar repositorio de GitHub a Railway
2. Railway detectará automáticamente los archivos `Procfile` y `railway.json`
3. Configurar variable de entorno `OPENAI_API_KEY` en Railway
4. Desplegar automáticamente

## 📁 Estructura del Proyecto

```
ChatBot-AI-main/
├── app.py                 # Aplicación principal Flask
├── requirements.txt       # Dependencias Python
├── Procfile              # Configuración Railway
├── railway.json          # Configuración deployment
├── .env.example          # Ejemplo variables entorno
├── data/                 # Base de conocimientos
├── static/               # Archivos estáticos
│   ├── css/
│   │   └── simple.css    # Estilos principales
│   ├── js/
│   │   └── app.js        # JavaScript frontend
│   ├── favicon.ico
│   └── JPlogo.png
└── templates/            # Templates HTML
    ├── index_v2.html     # Interfaz principal
    └── beta_expirada.html # Página expiración
```

## ⚙️ Configuración

### Variables de Entorno (.env)
```env
OPENAI_API_KEY=tu_api_key_de_openai
```

### Configuración de Producción
- Puerto por defecto: 5001
- Sistema beta activo hasta: 15 de agosto, 2025
- Localización: Español (Puerto Rico)

## 🤝 Contribuir

Este es un proyecto beta de la Junta de Planificación de Puerto Rico. Para contribuir:

1. Fork del proyecto
2. Crear rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Proyecto desarrollado para la Junta de Planificación de Puerto Rico.

## 📞 Contacto

Para soporte y consultas sobre el proyecto, contactar a través de los canales oficiales de la Junta de Planificación de Puerto Rico.

---

**⚠️ Nota**: Esta es una versión BETA que expira el 15 de agosto de 2025. No usar en producción sin autorización.
