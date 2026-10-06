/**
 * Máscaras e validações para campos numéricos
 */

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
    const dataInput = document.getElementById('data_nascimento');
    const telefoneInput = document.getElementById('telefone');
    
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

    // 2. Validação em tempo real
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

    // 3. Feedback visual ao focar nos campos
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

        // 4. Animação suave no submit
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('.btn-submit');
            if (submitBtn) {
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;
            }
        });
    }
});
