/**
 * Atividade Diária - JavaScript
 * Gerencia o registro de atividades diárias dos hábitos
 */

/**
 * Obtém o valor de um cookie
 * @param {string} name - Nome do cookie
 * @returns {string|null} - Valor do cookie ou null
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Altera a data selecionada e recarrega a página
 */
function alterarData() {
    const dataInput = document.getElementById('data_selecionada');
    if (!dataInput) return;
    
    const data = dataInput.value;
    // Usa a URL configurada ou constrói a partir da URL atual
    if (window.ATIVIDADE_DIARIA_URL) {
        window.location.href = window.ATIVIDADE_DIARIA_URL + '?data=' + data;
    } else {
        const url = new URL(window.location.href);
        url.searchParams.set('data', data);
        window.location.href = url.toString();
    }
}

/**
 * Altera a quantidade de um hábito
 * @param {number} habitoId - ID do hábito
 * @param {number} delta - Valor a ser adicionado/subtraído
 */
function alterarQuantidade(habitoId, delta) {
    const input = document.getElementById('quantidade_' + habitoId);
    if (!input) return;
    
    let valor = parseInt(input.value) || 0;
    valor = Math.max(0, valor + delta);
    input.value = valor;
    registrarAtividade(habitoId);
}

/**
 * Registra uma atividade para um hábito
 * @param {number} habitoId - ID do hábito
 */
function registrarAtividade(habitoId) {
    const input = document.getElementById('quantidade_' + habitoId);
    const dataInput = document.getElementById('data_selecionada');
    
    if (!input || !dataInput) return;
    
    const quantidade = parseInt(input.value) || 0;
    const data = dataInput.value;
    
    let csrfToken = getCookie('csrftoken');
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) csrfToken = csrfInput.value;
    
    // URL da API - configurada pelo Django template
    const apiUrl = window.REGISTRAR_ATIVIDADE_URL;
    if (!apiUrl) {
        console.error('URL de registrar atividade não configurada');
        return;
    }
    
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken || ''
        },
        body: JSON.stringify({
            habito_id: habitoId,
            quantidade: quantidade,
            data: data
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            atualizarInterfaceRegistro(input, data.quantidade);
        } else {
            alert('Erro ao registrar atividade: ' + (data.error || 'Erro desconhecido'));
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro ao registrar atividade. Tente novamente.');
    });
}

/**
 * Atualiza a interface após registrar uma atividade
 * @param {HTMLElement} input - Elemento input da quantidade
 * @param {number} quantidade - Quantidade registrada
 */
function atualizarInterfaceRegistro(input, quantidade) {
    const card = input.closest('.habito-registro-card');
    if (!card) return;
    
    let confirmacao = card.querySelector('.registro-confirmacao');
    if (!confirmacao) {
        confirmacao = document.createElement('div');
        confirmacao.className = 'registro-confirmacao';
        
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '20');
        svg.setAttribute('height', '20');
        svg.setAttribute('viewBox', '0 0 24 24');
        svg.innerHTML = '<path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
        
        const span = document.createElement('span');
        confirmacao.appendChild(svg);
        confirmacao.appendChild(span);
        
        const body = card.querySelector('.habito-registro-body');
        if (body) {
            body.appendChild(confirmacao);
        }
    }
    
    const span = confirmacao.querySelector('span');
    if (span) {
        span.textContent = 'Registrado: ' + quantidade + 'x';
    }
    
    // Feedback visual
    input.style.borderColor = '#10B981';
    setTimeout(() => {
        input.style.borderColor = '#E0E0E0';
    }, 1000);
}

// Auto-inicialização quando o DOM estiver pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        // Funções já estão disponíveis globalmente
    });
} else {
    // DOM já está pronto
}

