/**
 * Máscaras e validações para campos numéricos
 */

// Máscara para CPF: 000.000.000-00
function maskCPF(input) {
    let value = input.value.replace(/\D/g, ''); // Remove tudo que não é número
    
    if (value.length > 11) {
        value = value.slice(0, 11); // Limita a 11 dígitos
    }
    
    // Formata automaticamente
    if (value.length <= 3) {
        input.value = value;
    } else if (value.length <= 6) {
        input.value = value.slice(0, 3) + '.' + value.slice(3);
    } else if (value.length <= 9) {
        input.value = value.slice(0, 3) + '.' + value.slice(3, 6) + '.' + value.slice(6);
    } else {
        input.value = value.slice(0, 3) + '.' + value.slice(3, 6) + '.' + value.slice(6, 9) + '-' + value.slice(9);
    }
}

// Máscara para Data de Nascimento: dd/mm/aaaa
function maskDate(input) {
    let value = input.value.replace(/\D/g, ''); // Remove tudo que não é número
    
    if (value.length > 8) {
        value = value.slice(0, 8); // Limita a 8 dígitos
    }
    
    // Formata automaticamente
    if (value.length <= 2) {
        input.value = value;
    } else if (value.length <= 4) {
        input.value = value.slice(0, 2) + '/' + value.slice(2);
    } else {
        input.value = value.slice(0, 2) + '/' + value.slice(2, 4) + '/' + value.slice(4);
    }
}

// Máscara para Telefone: (11) 99999-9999
function maskPhone(input) {
    let value = input.value.replace(/\D/g, ''); // Remove tudo que não é número
    
    if (value.length > 11) {
        value = value.slice(0, 11); // Limita a 11 dígitos
    }
    
    // Formata automaticamente
    if (value.length <= 2) {
        input.value = value;
    } else if (value.length <= 7) {
        input.value = '(' + value.slice(0, 2) + ') ' + value.slice(2);
    } else {
        input.value = '(' + value.slice(0, 2) + ') ' + value.slice(2, 7) + '-' + value.slice(7);
    }
}

// Inicializa as máscaras quando o documento carrega
document.addEventListener('DOMContentLoaded', function() {
    const cpfInput = document.getElementById('cpf');
    const dataInput = document.getElementById('data_nascimento');
    const telefoneInput = document.getElementById('telefone');
    
    if (cpfInput) {
        cpfInput.addEventListener('input', function() {
            maskCPF(this);
        });
    }
    
    if (dataInput) {
        dataInput.addEventListener('input', function() {
            maskDate(this);
        });
    }
    
    if (telefoneInput) {
        telefoneInput.addEventListener('input', function() {
            maskPhone(this);
        });
    }
});

/**
 * Funcionalidades específicas para o formulário de cadastro de cliente
 */
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('cadastroForm');
    const passwordInput = document.getElementById('id_password');
    const togglePassword = document.getElementById('togglePassword');
    const cpfInput = document.getElementById('id_cpf');
    const emailInput = document.getElementById('id_email');
    const nomeInput = document.getElementById('id_nome_completo');
    const idadeInput = document.getElementById('id_idade');
    
    // 1. Toggle de visibilidade da senha
    if (togglePassword && passwordInput) {
        togglePassword.addEventListener('click', function(e) {
            e.preventDefault();
            const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordInput.setAttribute('type', type);
            
            const eyeSlash = document.getElementById('eye-slash');
            const eyeOpen = document.getElementById('eye-open');
            
            if (type === 'text') {
                eyeSlash.style.display = 'block';
                eyeOpen.style.opacity = '0.3';
            } else {
                eyeSlash.style.display = 'none';
                eyeOpen.style.opacity = '1';
            }
        });
    }

    // 2. Máscara de CPF (específica para o formulário de cadastro)
    if (cpfInput) {
        if (typeof maskCPF === 'function') {
            cpfInput.addEventListener('input', function() {
                maskCPF(this);
            });
        } else {
            // Fallback se maskCPF não estiver disponível
            cpfInput.addEventListener('input', function() {
                let value = this.value.replace(/\D/g, '');
                if (value.length > 11) value = value.slice(0, 11);
                
                if (value.length <= 3) {
                    this.value = value;
                } else if (value.length <= 6) {
                    this.value = value.slice(0, 3) + '.' + value.slice(3);
                } else if (value.length <= 9) {
                    this.value = value.slice(0, 3) + '.' + value.slice(3, 6) + '.' + value.slice(6);
                } else {
                    this.value = value.slice(0, 3) + '.' + value.slice(3, 6) + '.' + value.slice(6, 9) + '-' + value.slice(9);
                }
            });
        }
    }

    // 3. Validação em tempo real
    function validateField(input, validator) {
        const formGroup = input.closest('.form-group');
        if (!formGroup) return;
        
        const errorList = formGroup.querySelector('.errorlist');
        if (errorList) {
            errorList.remove();
        }
        
        if (input.value.trim() === '') {
            formGroup.classList.remove('valid', 'invalid');
            return;
        }
        
        const isValid = validator(input.value);
        formGroup.classList.toggle('valid', isValid);
        formGroup.classList.toggle('invalid', !isValid);
    }

    // Validação de email
    if (emailInput) {
        emailInput.addEventListener('blur', function() {
            validateField(this, (value) => {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                return emailRegex.test(value);
            });
        });
    }

    // Validação de idade
    if (idadeInput) {
        idadeInput.addEventListener('blur', function() {
            validateField(this, (value) => {
                const age = parseInt(value);
                return !isNaN(age) && age >= 0 && age <= 150;
            });
        });
    }

    // Função para validar CPF
    function validarCPF(cpf) {
        // Remove caracteres não numéricos
        cpf = cpf.replace(/\D/g, '');
        
        // Verifica se tem 11 dígitos
        if (cpf.length !== 11) {
            return false;
        }
        
        // Verifica se todos os dígitos são iguais (CPFs inválidos como 111.111.111-11)
        if (/^(\d)\1{10}$/.test(cpf)) {
            return false;
        }
        
        // Calcula o primeiro dígito verificador
        let soma = 0;
        for (let i = 0; i < 9; i++) {
            soma += parseInt(cpf.charAt(i)) * (10 - i);
        }
        let resto = soma % 11;
        let digito1 = resto < 2 ? 0 : 11 - resto;
        
        if (parseInt(cpf.charAt(9)) !== digito1) {
            return false;
        }
        
        // Calcula o segundo dígito verificador
        soma = 0;
        for (let i = 0; i < 10; i++) {
            soma += parseInt(cpf.charAt(i)) * (11 - i);
        }
        resto = soma % 11;
        let digito2 = resto < 2 ? 0 : 11 - resto;
        
        if (parseInt(cpf.charAt(10)) !== digito2) {
            return false;
        }
        
        return true;
    }

    // Validação de CPF em tempo real
    if (cpfInput) {
        cpfInput.addEventListener('blur', function() {
            const cpfValue = this.value;
            const isValid = validarCPF(cpfValue);
            
            const formGroup = this.closest('.form-group');
            if (!formGroup) return;
            
            // Remove mensagens de erro anteriores
            let errorList = formGroup.querySelector('.errorlist');
            if (errorList) {
                errorList.remove();
            }
            
            // Remove mensagem de erro customizada se existir
            let customError = formGroup.querySelector('.cpf-error-message');
            if (customError) {
                customError.remove();
            }
            
            if (cpfValue.trim() === '') {
                formGroup.classList.remove('valid', 'invalid');
                return;
            }
            
            if (!isValid) {
                formGroup.classList.add('invalid');
                formGroup.classList.remove('valid');
                
                // Adiciona mensagem de erro customizada
                const errorMsg = document.createElement('div');
                errorMsg.className = 'cpf-error-message';
                errorMsg.style.color = '#EF4444';
                errorMsg.style.fontSize = '0.875rem';
                errorMsg.style.marginTop = '4px';
                errorMsg.textContent = 'CPF inválido. Por favor, digite um CPF válido.';
                formGroup.appendChild(errorMsg);
            } else {
                formGroup.classList.add('valid');
                formGroup.classList.remove('invalid');
            }
        });
        
        // Validação também no submit do formulário
        if (form) {
            form.addEventListener('submit', function(e) {
                const cpfValue = cpfInput.value;
                if (cpfValue.trim() !== '' && !validarCPF(cpfValue)) {
                    e.preventDefault();
                    cpfInput.focus();
                    cpfInput.dispatchEvent(new Event('blur'));
                    return false;
                }
            });
        }
    }

    // 4. Feedback visual ao focar nos campos
    if (form) {
        const inputs = form.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.closest('.form-group')?.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                this.closest('.form-group')?.classList.remove('focused');
            });
        });

        // 5. Animação suave no submit
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('.btn-submit');
            if (submitBtn) {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
            }
        });
    }
});