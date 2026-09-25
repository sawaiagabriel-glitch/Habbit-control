/**
 * Progressos - JavaScript
 * Gerencia notificações na página de progressos
 */

/**
 * Inicializa notificações toast com auto-dismiss
 */
function inicializarNotificacoes() {
    const successMessages = document.querySelectorAll('.message-toast-top.message-toast-success');
    const errorMessages = document.querySelectorAll('.message-toast-top.message-toast-error');
    
    // Notificações de sucesso
    successMessages.forEach(function(message, index) {
        setTimeout(function() {
            message.classList.add('fade-out');
            setTimeout(function() {
                message.remove();
            }, 500);
        }, 5000 + (index * 200));
    });
    
    // Notificações de erro
    errorMessages.forEach(function(message, index) {
        setTimeout(function() {
            message.classList.add('fade-out');
            setTimeout(function() {
                message.remove();
            }, 500);
        }, 5000 + (index * 200));
    });
}

// Auto-inicialização quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        inicializarNotificacoes();
    });
} else {
    inicializarNotificacoes();
}

