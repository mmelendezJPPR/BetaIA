// ===== VARIABLES GLOBALES =====
let currentSessionId = null;

// ===== INICIALIZACIÓN =====
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Generar ID de sesión único
    currentSessionId = generateSessionId();
    
    // Configurar event listeners
    setupEventListeners();
    
    // Configurar auto-resize del textarea
    setupTextareaAutoResize();
    
    // Cargar historial si existe
    loadChatHistory();
    
    // Focus inicial
    const userInputElement = document.getElementById('userInput');
    if (userInputElement) userInputElement.focus();
}

// ===== EVENT LISTENERS =====
function setupEventListeners() {
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const clearBtn = document.getElementById('clearChat');
    const exportBtn = document.getElementById('exportChat');
    const attachBtn = document.getElementById('attachBtn');
    
    // Envío de mensajes
    if (sendBtn) sendBtn.addEventListener('click', handleSendMessage);
    if (userInput) userInput.addEventListener('keydown', handleKeyDown);
    
    // Acciones del chat
    if (clearBtn) clearBtn.addEventListener('click', clearChat);
    if (exportBtn) exportBtn.addEventListener('click', exportChat);
    if (attachBtn) attachBtn.addEventListener('click', handleAttachment);
    
    // Contador de caracteres
    if (userInput) userInput.addEventListener('input', updateCharacterCount);
    
    // Modal events
    setupModalEvents();
}

function setupModalEvents() {
    const modal = document.getElementById('helpModal');
    if (!modal) return;
    
    const closeBtn = modal.querySelector('.close');
    
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// ===== MANEJO DE MENSAJES =====
function handleKeyDown(e) {
    if (e.key === 'Enter') {
        if (e.shiftKey) {
            // Permitir nueva línea con Shift+Enter
            return;
        } else {
            e.preventDefault();
            handleSendMessage();
        }
    }
}

async function handleSendMessage() {
    const userInput = document.getElementById('userInput');
    const message = userInput.value.trim();
    
    if (!message) return;
    
    // Limpiar input y deshabilitar envío
    userInput.value = '';
    updateCharacterCount();
    setInputState(false);
    
    // Mostrar mensaje del usuario
    addMessage(message, 'user');
    
    // Mostrar indicador de escritura
    showTypingIndicator();
    
    try {
        // Enviar a la API
        const response = await sendToAPI(message);
        
        // Ocultar indicador de escritura
        hideTypingIndicator();
        
        // Mostrar respuesta del bot
        addMessage(response, 'bot');
        
        // Guardar en historial
        saveChatHistory();
        
    } catch (error) {
        hideTypingIndicator();
        addMessage('❌ Lo siento, ocurrió un error. Por favor, intenta nuevamente.', 'bot', true);
        console.error('Error:', error);
    } finally {
        setInputState(true);
        userInput.focus();
    }
}

async function sendToAPI(message) {
    const response = await fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            session_id: currentSessionId
        })
    });
    
    if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    return data.response || 'Lo siento, no pude procesar tu consulta.';
}

function sendQuickMessage(message) {
    const userInput = document.getElementById('userInput');
    userInput.value = message;
    handleSendMessage();
}

// ===== MANEJO DE MENSAJES EN UI =====
function addMessage(content, sender, isError = false) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    const timestamp = new Date().toLocaleTimeString('es-PR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    messageDiv.className = `message ${sender}-message`;
    if (isError) messageDiv.classList.add('error-message');
    
    const avatarIcon = sender === 'bot' ? 'fas fa-gavel' : 'fas fa-user';
    const senderName = sender === 'bot' ? 'Agente de planificacion' : 'Tú';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="${avatarIcon}"></i>
        </div>
        <div class="message-content">
            <div class="message-header">
                <span class="sender-name">${senderName}</span>
                <span class="message-time">${timestamp}</span>
            </div>
            <div class="message-text">
                ${formatMessageContent(content)}
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
}

function formatMessageContent(content) {
    // Convertir markdown básico a HTML
    return content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>')
        .replace(/`(.*?)`/g, '<code>$1</code>');
}

function showTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    indicator.style.display = 'flex';
    scrollToBottom();
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    indicator.style.display = 'none';
}

function scrollToBottom() {
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ===== UTILIDADES DE INPUT =====
function updateCharacterCount() {
    const userInput = document.getElementById('userInput');
    const charCount = document.getElementById('charCount');
    const count = userInput.value.length;
    
    charCount.textContent = count;
    charCount.style.color = count > 900 ? '#e74c3c' : 'var(--text-secondary)';
}

function setupTextareaAutoResize() {
    const textarea = document.getElementById('userInput');
    
    textarea.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
}

function setInputState(enabled) {
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    
    userInput.disabled = !enabled;
    sendBtn.disabled = !enabled;
    
    if (enabled) {
        sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
    } else {
        sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    }
}

// ===== FUNCIONES DE CHAT =====
function clearChat() {
    if (confirm('¿Estás seguro de que quieres limpiar toda la conversación?')) {
        const messagesContainer = document.getElementById('chatMessages');
        
        // Mantener solo el mensaje de bienvenida
        const welcomeMessage = messagesContainer.querySelector('.welcome-message').parentElement;
        messagesContainer.innerHTML = '';
        messagesContainer.appendChild(welcomeMessage);
        
        // Limpiar historial
        localStorage.removeItem(`chat_history_${currentSessionId}`);
        
        // Nuevo ID de sesión
        currentSessionId = generateSessionId();
        
        // Mostrar notificación
        showNotification('Conversación limpiada', 'success');
    }
}

function exportChat() {
    const messages = document.querySelectorAll('.message:not(.welcome-message)');
    let chatText = `Conversación Agente de planificacion - ${new Date().toLocaleString('es-PR')}\n`;
    chatText += '='.repeat(60) + '\n\n';
    
    messages.forEach(message => {
        const sender = message.querySelector('.sender-name').textContent;
        const time = message.querySelector('.message-time').textContent;
        const content = message.querySelector('.message-text').textContent;
        
        chatText += `[${time}] ${sender}:\n${content}\n\n`;
    });
    
    // Crear y descargar archivo
    const blob = new Blob([chatText], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Agente de planificacion_Chat_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification('Conversación exportada', 'success');
}

function handleAttachment() {
    showNotification('Función de adjuntos próximamente disponible', 'info');
}

// ===== HISTORIAL Y PERSISTENCIA =====
function saveChatHistory() {
    try {
        const messages = [];
        const messageElements = document.querySelectorAll('.message:not(.welcome-message)');
        
        messageElements.forEach(element => {
            const sender = element.classList.contains('user-message') ? 'user' : 'bot';
            const content = element.querySelector('.message-text').textContent;
            const time = element.querySelector('.message-time').textContent;
            
            messages.push({ sender, content, time });
        });
        
        localStorage.setItem(`chat_history_${currentSessionId}`, JSON.stringify(messages));
    } catch (error) {
        console.warn('No se pudo guardar el historial:', error);
    }
}

function loadChatHistory() {
    try {
        const savedHistory = localStorage.getItem(`chat_history_${currentSessionId}`);
        if (savedHistory) {
            const messages = JSON.parse(savedHistory);
            messages.forEach(message => {
                addMessage(message.content, message.sender);
            });
        }
    } catch (error) {
        console.warn('No se pudo cargar el historial:', error);
    }
}


 

// ===== UTILIDADES =====
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Estilos inline para la notificación
    Object.assign(notification.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        padding: '1rem 1.5rem',
        borderRadius: '8px',
        color: 'white',
        fontWeight: '500',
        zIndex: '3000',
        animation: 'slideInRight 0.3s ease',
        backgroundColor: type === 'success' ? '#2ecc71' : 
                         type === 'error' ? '#e74c3c' : '#3498db'
    });
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// ===== FUNCIONES DE MODAL =====
function showHelp() {
    const modal = document.getElementById('helpModal');
    if (modal) modal.style.display = 'block';
}

function showPrivacy() {
    showNotification('Política de privacidad próximamente disponible', 'info');
}

// ===== ANIMACIONES CSS ADICIONALES =====
const additionalStyles = `
@keyframes slideInRight {
    from {
        opacity: 0;
        transform: translateX(100px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes slideOutRight {
    from {
        opacity: 1;
        transform: translateX(0);
    }
    to {
        opacity: 0;
        transform: translateX(100px);
    }
}

.error-message .message-text {
    background: #ffe6e6 !important;
    border-color: #e74c3c !important;
    color: #c0392b !important;
}

.notification {
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
`;

// Inyectar estilos adicionales
const styleSheet = document.createElement('style');
styleSheet.textContent = additionalStyles;
document.head.appendChild(styleSheet);

// ===== MANEJO DE ERRORES GLOBALES =====
//window.addEventListener('error', function(e) {
   // console.error('Error global:', e.error);
   // showNotification('Ocurrió un error inesperado', 'error');
//});

// ===== CONFIGURACIÓN DE PERFORMANCE =====
// Debounce para el auto-guardado
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Auto-guardado con debounce
const debouncedSave = debounce(saveChatHistory, 1000);

// ===== ACCESIBILIDAD =====
document.addEventListener('keydown', function(e) {
    // Atajos de teclado
    if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
            case 'k':
                e.preventDefault();
                const userInput = document.getElementById('userInput');
                if (userInput) userInput.focus();
                break;
            case 'l':
                e.preventDefault();
                clearChat();
                break;
            case 's':
                e.preventDefault();
                exportChat();
                break;
        }
    }
    
    // Escape para cerrar modal
    if (e.key === 'Escape') {
        const modal = document.getElementById('helpModal');
        if (modal.style.display === 'block') {
            modal.style.display = 'none';
        }
    }
});

console.log('🚀 Agente de planificacion ChatBot initialized successfully!');
