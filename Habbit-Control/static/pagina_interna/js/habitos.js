/**
 * Hábitos - JavaScript
 * Gerencia cadastro e edição de hábitos
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

/**
 * Gerencia modal de confirmação de exclusão
 */
const ModalExclusao = {
    modal: null,
    
    init: function() {
        this.modal = document.getElementById('modalExclusao');
        if (!this.modal) return;
        
        // Fecha o modal ao clicar fora dele
        this.modal.addEventListener('click', function(e) {
            if (e.target === this) {
                ModalExclusao.fechar();
            }
        });
        
        // Fecha o modal com a tecla ESC
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                ModalExclusao.fechar();
            }
        });
    },
    
    abrir: function() {
        if (this.modal) {
            this.modal.style.display = 'flex';
        }
    },
    
    fechar: function() {
        if (this.modal) {
            this.modal.style.display = 'none';
        }
    },
    
    confirmar: function() {
        this.fechar();
        const deleteForm = document.getElementById('deleteForm');
        if (deleteForm) {
            deleteForm.submit();
        }
    }
};

// Funções globais para compatibilidade com onclick inline
function abrirModal() {
    ModalExclusao.abrir();
}

function fecharModal() {
    ModalExclusao.fechar();
}

function confirmarExclusao() {
    ModalExclusao.confirmar();
}

// Auto-inicialização quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        inicializarNotificacoes();
        ModalExclusao.init();
    });
} else {
    inicializarNotificacoes();
    ModalExclusao.init();
}

