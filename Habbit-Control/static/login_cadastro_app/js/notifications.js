/**
 * Gerenciamento de notificações toast
 * Auto-dismiss com fade out
 */

/**
 * Inicializa o auto-dismiss das notificações
 * @param {string} selector - Seletor CSS para as notificações
 * @param {number} delay - Delay em milissegundos antes de iniciar o fade out
 */
function inicializarNotificacoes(selector = '.message-toast-top', delay = 5000) {
    const messages = document.querySelectorAll(selector);
    
    messages.forEach(function(message, index) {
        setTimeout(function() {
            message.classList.add('fade-out');
            setTimeout(function() {
                message.remove();
            }, 500); // Tempo da animação de fade out
        }, delay + (index * 200)); // Delay + delay entre múltiplas mensagens
    });
}

// Auto-inicialização quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        inicializarNotificacoes('.message-toast-top.message-toast-error');
        inicializarNotificacoes('.message-toast-top.message-toast-success');
    });
} else {
    inicializarNotificacoes('.message-toast-top.message-toast-error');
    inicializarNotificacoes('.message-toast-top.message-toast-success');
}

