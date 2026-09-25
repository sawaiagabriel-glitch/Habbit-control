/**
 * Funcionalidade de edição de dados no perfil do cliente
 * Arquivo: edit_profile.js
 */

document.addEventListener('DOMContentLoaded', function() {
    setupEditableFields();
});

function setupEditableFields() {
    const editableFields = document.querySelectorAll('.info-field.editable');
    
    editableFields.forEach(field => {
        const editIcon = field.querySelector('.edit-icon');
        
        if (editIcon) {
            editIcon.style.cursor = 'pointer';
            
            editIcon.addEventListener('click', function(e) {
                e.stopPropagation();
                handleEditClick(field);
            });
        }
    });
}

function handleEditClick(field) {
    const input = field.querySelector('input, select, textarea');
    
    if (input) {
        // Já está em modo edição - salvar
        saveField(field);
    } else {
        // Ativar modo edição
        enterEditMode(field);
    }
}

function enterEditMode(field) {
    const fieldLabel = field.querySelector('.field-label');
    const fieldValue = field.querySelector('.field-value');
    
    const currentDisplayValue = fieldValue.textContent.trim();
    const fieldName = extractFieldName(fieldLabel.textContent);
    
    // Container para o input (necessário para posicionar o olhinho da senha)
    const inputContainer = document.createElement('div');
    inputContainer.className = 'input-container';
    inputContainer.style.position = 'relative';
    inputContainer.style.width = '100%';
    
    // Cria o elemento de input
    let inputElement = document.createElement('input');
    
    // Configuração específica por tipo de campo
    if (fieldName === 'password') {
        inputElement.type = 'password';
        inputElement.placeholder = 'Digite a nova senha';
        inputElement.value = ''; // Senha começa vazia
        inputElement.style.paddingRight = '35px'; // Espaço para o ícone do olho
        
        // Cria o ícone do olho
        const eyeIcon = document.createElement('span');
        eyeIcon.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#666" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
            </svg>
        `;
        eyeIcon.style.position = 'absolute';
        eyeIcon.style.right = '10px';
        eyeIcon.style.top = '50%';
        eyeIcon.style.transform = 'translateY(-50%)';
        eyeIcon.style.cursor = 'pointer';
        eyeIcon.style.display = 'flex';
        eyeIcon.style.zIndex = '10'; // Garante que fique acima do input
        
        // Função para alternar visibilidade
        eyeIcon.addEventListener('mousedown', function(e) {
            // mousedown previne que o input perca o foco (blur)
            e.preventDefault(); 
            
            if (inputElement.type === 'password') {
                inputElement.type = 'text';
                // Ícone de olho cortado (senha visível)
                eyeIcon.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#666" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                        <line x1="1" y1="1" x2="23" y2="23"></line>
                    </svg>
                `;
            } else {
                inputElement.type = 'password';
                // Ícone de olho normal (senha oculta)
                eyeIcon.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#666" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                `;
            }
        });
        
        inputContainer.appendChild(eyeIcon);
    } else if (fieldName === 'idade') {
        inputElement.type = 'number';
        inputElement.value = currentDisplayValue;
    } else if (fieldName === 'email') {
        inputElement.type = 'email';
        inputElement.value = currentDisplayValue;
    } else {
        inputElement.type = 'text';
        inputElement.value = currentDisplayValue;
    }
    
    inputElement.className = 'edit-input';
    
    // Estilos do input
    inputElement.style.width = '100%';
    inputElement.style.padding = '8px 12px';
    if (fieldName === 'password') inputElement.style.paddingRight = '35px'; // Ajuste se for senha
    inputElement.style.border = '1px solid #2C2C4A';
    inputElement.style.borderRadius = '6px';
    inputElement.style.fontSize = '1rem';
    inputElement.style.fontFamily = 'inherit';
    inputElement.style.backgroundColor = '#fff';
    
    // Adiciona o input ao container
    inputContainer.appendChild(inputElement);
    
    // Substitui o valor visual pelo container com o input
    fieldValue.replaceWith(inputContainer);
    
    inputElement.focus();
    
    // Eventos de Teclado
    inputElement.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            saveField(field);
        } else if (e.key === 'Escape') {
            cancelEdit(field, currentDisplayValue);
        }
    });
    
    // Evento ao sair do campo (Blur)
    inputElement.addEventListener('blur', function() {
        setTimeout(() => {
            // Verifica se o input ainda está lá (e não foi removido pelo saveField)
            if (field.contains(inputElement)) {
                saveField(field);
            }
        }, 150); // Delay um pouco maior para garantir que cliques não se percam
    });
}

function saveField(field) {
    const fieldLabel = field.querySelector('.field-label');
    const input = field.querySelector('input, select, textarea');
    
    if (!input) return;
    
    let newValue = input.value.trim();
    const fieldName = extractFieldName(fieldLabel.textContent);
    
    // Se for senha vazia, cancela a edição
    if (fieldName === 'password' && newValue === '') {
        cancelEdit(field, '********');
        return;
    }

    const displayValue = formatFieldForDisplay(fieldName, newValue);
    
    // Cria o novo span com o valor
    const newFieldValue = document.createElement('span');
    newFieldValue.className = 'field-value';
    newFieldValue.textContent = displayValue || '(vazio)';
    
    // O input está dentro de um .input-container agora?
    const container = field.querySelector('.input-container');
    if (container) {
        container.replaceWith(newFieldValue);
    } else {
        // Fallback caso não tenha container (edição antiga)
        input.replaceWith(newFieldValue);
    }
    
    saveToBackend(fieldName, newValue, field);
}

function formatFieldForDisplay(fieldName, value) {
    if (fieldName === 'password') {
        return '********'; 
    }
    return value;
}

function cancelEdit(field, originalValue) {
    const container = field.querySelector('.input-container');
    const input = field.querySelector('input, select, textarea');
    
    const newFieldValue = document.createElement('span');
    newFieldValue.className = 'field-value';
    newFieldValue.textContent = originalValue;

    if (container) {
        container.replaceWith(newFieldValue);
    } else if (input) {
        input.replaceWith(newFieldValue);
    }
}

function extractFieldName(labelText) {
    const normalized = labelText.toLowerCase().trim();
    
    const labelMap = {
        'nome completo': 'nome_completo',
        'idade': 'idade',
        'cpf': 'cpf',
        'email': 'email',
        'senha': 'password',
        'cidade': 'cidade',
        'país': 'pais',
        'pais': 'pais',
        'profissão': 'profissao',
        'profissao': 'profissao'
    };

    if (labelMap[normalized]) {
        return labelMap[normalized];
    }
    
    return normalized.replace(/\s+/g, '_');
}

function saveToBackend(fieldName, value, field) {
    let csrfToken = null;
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) csrfToken = csrfInput.value;
    if (!csrfToken) csrfToken = getCookie('csrftoken');
    
    const fieldMap = {
        'nome_completo': 'nome_completo',
        'idade': 'idade',
        'cpf': 'cpf',
        'email': 'email',
        'password': 'password',
        'cidade': 'cidade',
        'pais': 'pais',
        'profissao': 'profissao'
    };
    
    const modelField = fieldMap[fieldName] || fieldName;
    
    const fieldValue = field.querySelector('.field-value');
    const originalColor = fieldValue ? fieldValue.style.color : '';
    
    fetch('/api/cliente/update/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken || ''
        },
        body: JSON.stringify({
            field: modelField,
            value: value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (fieldValue) {
                fieldValue.style.color = '#27AE60'; 
                setTimeout(() => {
                    fieldValue.style.color = originalColor;
                }, 1500);
            }
        } else {
            console.error('Erro ao salvar:', data.error);
            if (fieldValue) {
                fieldValue.style.color = '#E74C3C';
                setTimeout(() => {
                    fieldValue.style.color = originalColor;
                }, 1500);
            }
        }
    })
    .catch(error => {
        console.error('Erro na requisição:', error);
        if (fieldValue) {
            fieldValue.style.color = '#E74C3C';
        }
    });
}

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