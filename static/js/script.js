// Funções utilitárias
function previewImage(input) {
    if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('preview').src = e.target.result;
        }
        reader.readAsDataURL(input.files[0]);
    }
}

// Máscaras para campos formatados
function applyMasks() {
    // CPF
    const cpfInputs = document.querySelectorAll('input[data-mask="cpf"]');
    cpfInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 11) {
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d)/, '$1.$2');
                value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
                e.target.value = value;
            }
        });
    });

    // Telefone
    const phoneInputs = document.querySelectorAll('input[data-mask="phone"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 11) {
                value = value.replace(/(\d{2})(\d)/, '($1) $2');
                value = value.replace(/(\d{5})(\d)/, '$1-$2');
                e.target.value = value;
            }
        });
    });

    // Data
    const dateInputs = document.querySelectorAll('input[data-mask="date"]');
    dateInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length <= 8) {
                value = value.replace(/(\d{2})(\d)/, '$1/$2');
                value = value.replace(/(\d{2})(\d)/, '$1/$2');
                e.target.value = value;
            }
        });
    });
}

// Validação em tempo real
function setupRealTimeValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('input', function() {
                validateField(this);
            });
            input.addEventListener('blur', function() {
                validateField(this);
            });
        });
    });
}

function validateField(field) {
    const value = field.value.trim();
    let isValid = true;
    let errorMessage = '';

    // Validação de email
    if (field.type === 'email') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Por favor, insira um email válido';
        }
    }

    // Validação de CPF
    if (field.dataset.mask === 'cpf') {
        const cpf = value.replace(/\D/g, '');
        if (cpf.length !== 11) {
            isValid = false;
            errorMessage = 'CPF deve conter 11 dígitos';
        }
    }

    // Validação de telefone
    if (field.dataset.mask === 'phone') {
        const phone = value.replace(/\D/g, '');
        if (phone.length < 10 || phone.length > 11) {
            isValid = false;
            errorMessage = 'Telefone deve conter 10 ou 11 dígitos';
        }
    }

    // Validação de data
    if (field.dataset.mask === 'date') {
        const date = value.split('/');
        if (date.length === 3) {
            const day = parseInt(date[0]);
            const month = parseInt(date[1]);
            const year = parseInt(date[2]);
            const dateObj = new Date(year, month - 1, day);
            if (dateObj.getDate() !== day || dateObj.getMonth() !== month - 1 || dateObj.getFullYear() !== year) {
                isValid = false;
                errorMessage = 'Data inválida';
            }
        }
    }

    // Validação de campos obrigatórios
    if (field.required && !value) {
        isValid = false;
        errorMessage = 'Este campo é obrigatório';
    }

    // Atualizar feedback visual
    const feedback = field.nextElementSibling;
    if (feedback && feedback.classList.contains('invalid-feedback')) {
        if (!isValid) {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
            feedback.textContent = errorMessage;
        } else {
            field.classList.add('is-valid');
            field.classList.remove('is-invalid');
            feedback.textContent = '';
        }
    }

    return isValid;
}

// Confirmação de ações críticas
function setupConfirmations() {
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    // Aplicar máscaras
    applyMasks();

    // Configurar validação em tempo real
    setupRealTimeValidation();

    // Configurar confirmações
    setupConfirmations();

    // Validação de formulários com classe 'needs-validation'
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Inicialização de tooltips do Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}); 