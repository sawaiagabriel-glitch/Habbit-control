/**
 * Edição inline do perfil do cliente
 * Usa /api/cliente/update/ (update_cliente) com CSRF.
 */

document.addEventListener('DOMContentLoaded', function() {
    setupEditableFields();
});

function setupEditableFields() {
    document.querySelectorAll('.info-field.editable').forEach(field => {
        const editIcon = field.querySelector('.edit-icon');
        if (!editIcon) return;

        editIcon.style.cursor = 'pointer';
        editIcon.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            if (field.classList.contains('is-editing')) {
                return;
            }
            enterEditMode(field);
        });
    });
}

function getFieldName(field) {
    return field.dataset.field || '';
}

function getCurrentEstado() {
    const estadoField = document.querySelector('.info-field[data-field="estado"] .field-value');
    return estadoField ? estadoField.textContent.trim() : '';
}

function showToast(message, type) {
    const toast = document.getElementById('profile-toast');
    if (!toast) return;

    toast.hidden = false;
    toast.textContent = message;
    toast.className = 'profile-toast profile-toast-' + (type || 'info');

    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(() => {
        toast.hidden = true;
    }, 3500);
}

function enterEditMode(field) {
    // Fecha qualquer outra edição aberta
    document.querySelectorAll('.info-field.is-editing').forEach(other => {
        if (other !== field) {
            const original = other.dataset.originalValue;
            cancelEdit(other, original !== undefined ? original : '');
        }
    });

    const fieldValue = field.querySelector('.field-value');
    if (!fieldValue) return;

    const fieldName = getFieldName(field);
    const currentDisplayValue = fieldValue.textContent.trim();
    field.dataset.originalValue = currentDisplayValue;
    field.classList.add('is-editing');

    const editArea = document.createElement('div');
    editArea.className = 'field-edit-area';

    const inputContainer = document.createElement('div');
    inputContainer.className = 'input-container';

    let inputElement;

    if (fieldName === 'estado' && typeof estadosECidades !== 'undefined') {
        inputElement = document.createElement('select');
        inputElement.className = 'edit-input';
        const emptyOpt = document.createElement('option');
        emptyOpt.value = '';
        emptyOpt.textContent = 'Selecione o estado';
        inputElement.appendChild(emptyOpt);

        Object.keys(estadosECidades).sort(function(a, b) {
            const nomes = typeof nomesEstados !== 'undefined' ? nomesEstados : {};
            return (nomes[a] || a).localeCompare(nomes[b] || b);
        }).forEach(function(sigla) {
            const option = document.createElement('option');
            option.value = sigla;
            option.textContent = (typeof nomesEstados !== 'undefined' && nomesEstados[sigla])
                ? nomesEstados[sigla] + ' (' + sigla + ')'
                : sigla;
            if (sigla === currentDisplayValue) {
                option.selected = true;
            }
            inputElement.appendChild(option);
        });
    } else if (fieldName === 'cidade' && typeof estadosECidades !== 'undefined') {
        const estadoAtual = getCurrentEstado();
        inputElement = document.createElement('select');
        inputElement.className = 'edit-input';

        if (!estadoAtual || !estadosECidades[estadoAtual]) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Selecione um estado primeiro';
            option.disabled = true;
            option.selected = true;
            inputElement.appendChild(option);
            inputElement.disabled = true;
        } else {
            const placeholder = document.createElement('option');
            placeholder.value = '';
            placeholder.textContent = 'Selecione a cidade';
            inputElement.appendChild(placeholder);

            estadosECidades[estadoAtual].slice().sort().forEach(function(cidade) {
                const option = document.createElement('option');
                option.value = cidade;
                option.textContent = cidade;
                if (cidade === currentDisplayValue) {
                    option.selected = true;
                }
                inputElement.appendChild(option);
            });
        }
    } else {
        inputElement = document.createElement('input');
        inputElement.className = 'edit-input';

        if (fieldName === 'password') {
            inputElement.type = 'password';
            inputElement.placeholder = 'Digite a nova senha';
            inputElement.value = '';
            inputElement.autocomplete = 'new-password';
            addPasswordToggle(inputContainer, inputElement);
        } else if (fieldName === 'idade') {
            inputElement.type = 'number';
            inputElement.min = '0';
            inputElement.step = '1';
            inputElement.value = currentDisplayValue;
        } else if (fieldName === 'email') {
            inputElement.type = 'email';
            inputElement.value = currentDisplayValue;
        } else {
            inputElement.type = 'text';
            inputElement.value = currentDisplayValue;
        }
    }

    inputContainer.appendChild(inputElement);

    const actions = document.createElement('div');
    actions.className = 'field-edit-actions';

    const btnSave = document.createElement('button');
    btnSave.type = 'button';
    btnSave.className = 'btn-field-save';
    btnSave.textContent = 'Salvar';

    const btnCancel = document.createElement('button');
    btnCancel.type = 'button';
    btnCancel.className = 'btn-field-cancel';
    btnCancel.textContent = 'Cancelar';

    actions.appendChild(btnSave);
    actions.appendChild(btnCancel);

    editArea.appendChild(inputContainer);
    editArea.appendChild(actions);
    fieldValue.replaceWith(editArea);

    if (!inputElement.disabled) {
        inputElement.focus();
    }

    btnSave.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        saveField(field);
    });

    btnCancel.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        cancelEdit(field, field.dataset.originalValue || '');
    });

    inputElement.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && inputElement.tagName !== 'SELECT') {
            e.preventDefault();
            saveField(field);
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelEdit(field, field.dataset.originalValue || '');
        }
    });
}

function addPasswordToggle(container, inputElement) {
    container.style.position = 'relative';
    inputElement.style.paddingRight = '40px';

    const eyeIcon = document.createElement('button');
    eyeIcon.type = 'button';
    eyeIcon.className = 'password-toggle-btn';
    eyeIcon.setAttribute('aria-label', 'Mostrar senha');
    eyeIcon.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#666" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
            <circle cx="12" cy="12" r="3"></circle>
        </svg>
    `;

    eyeIcon.addEventListener('mousedown', function(e) {
        e.preventDefault();
        if (inputElement.type === 'password') {
            inputElement.type = 'text';
            eyeIcon.setAttribute('aria-label', 'Ocultar senha');
        } else {
            inputElement.type = 'password';
            eyeIcon.setAttribute('aria-label', 'Mostrar senha');
        }
    });

    container.appendChild(eyeIcon);
}

function restoreFieldValue(field, displayValue) {
    const editArea = field.querySelector('.field-edit-area');
    const newFieldValue = document.createElement('span');
    newFieldValue.className = 'field-value';
    newFieldValue.textContent = displayValue;

    if (editArea) {
        editArea.replaceWith(newFieldValue);
    }

    field.classList.remove('is-editing');
    delete field.dataset.originalValue;
}

function cancelEdit(field, originalValue) {
    const fieldName = getFieldName(field);
    const display = fieldName === 'password' ? '********' : (originalValue || '');
    restoreFieldValue(field, display);
}

function formatFieldForDisplay(fieldName, value) {
    if (fieldName === 'password') {
        return '********';
    }
    return value;
}

function saveField(field) {
    const input = field.querySelector('input, select, textarea');
    if (!input || input.disabled) return;

    const fieldName = getFieldName(field);
    const originalValue = field.dataset.originalValue || '';
    let newValue = input.value.trim();

    if (fieldName === 'password' && newValue === '') {
        cancelEdit(field, '********');
        return;
    }

    if (fieldName === 'nome_completo' && newValue === '') {
        showToast('O nome completo não pode ficar vazio.', 'error');
        return;
    }

    // Desabilita botões durante o request
    const btnSave = field.querySelector('.btn-field-save');
    const btnCancel = field.querySelector('.btn-field-cancel');
    if (btnSave) btnSave.disabled = true;
    if (btnCancel) btnCancel.disabled = true;
    input.disabled = true;

    saveToBackend(fieldName, newValue)
        .then(data => {
            if (data.success) {
                const displayValue = formatFieldForDisplay(
                    fieldName,
                    data.value !== undefined && data.value !== null ? String(data.value) : newValue
                );
                restoreFieldValue(field, displayValue);
                showToast(data.message || 'Dados atualizados com sucesso', 'success');

                // Se o estado mudou, a cidade pode ficar inconsistente — limpa visualmente
                // apenas se o usuário salvou um estado diferente (cidade continua no banco
                // até ser editada; não criamos regra de negócio nova no backend).
            } else {
                cancelEdit(field, originalValue);
                showToast(data.error || 'Erro ao salvar.', 'error');
            }
        })
        .catch(error => {
            console.error('Erro na requisição:', error);
            cancelEdit(field, originalValue);
            showToast('Erro ao salvar. Tente novamente.', 'error');
        });
}

function saveToBackend(fieldName, value) {
    let csrfToken = null;
    const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrfInput) csrfToken = csrfInput.value;
    if (!csrfToken) csrfToken = getCookie('csrftoken');

    const allowed = {
        'nome_completo': 'nome_completo',
        'idade': 'idade',
        'email': 'email',
        'password': 'password',
        'cidade': 'cidade',
        'estado': 'estado'
    };

    if (!allowed[fieldName]) {
        return Promise.resolve({ success: false, error: 'Campo não permitido' });
    }

    const apiUrl = window.UPDATE_CLIENTE_URL || '/api/cliente/update/';

    return fetch(apiUrl, {
        method: 'POST',
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken || ''
        },
        body: JSON.stringify({
            field: allowed[fieldName],
            value: value
        })
    }).then(response => response.json().then(data => {
        // Propaga status útil mesmo quando success=false
        if (!response.ok && !data.error) {
            data.error = 'Erro ao salvar';
            data.success = false;
        }
        return data;
    }));
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
