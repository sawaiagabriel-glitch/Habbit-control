from django import forms
from .models import Cliente
from django.contrib.auth.hashers import make_password
import re

def validar_cpf(cpf):
    """
    Valida CPF verificando os dígitos verificadores.
    Retorna True se o CPF for válido, False caso contrário.
    """
    # Remove caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    if len(cpf) != 11:
        return False
    
    if cpf == cpf[0] * 11:
        return False
    
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[9]) != digito1:
        return False
    
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[10]) != digito2:
        return False
    
    return True

class ClienteForm(forms.ModelForm):
    # Sobrescreve o campo Senha para usar o Widget de Senha (oculta o texto)
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={'placeholder': 'Digite sua senha'}),
        max_length=100,
        required=True
    )
    
    class Meta:
        model = Cliente
        fields = ['nome_completo', 'idade', 'cpf', 'email', 'password', 'estado', 'cidade', 'profissao', 'lgpd']
        
        widgets = {
            'nome_completo': forms.TextInput(attrs={'placeholder': 'Seu nome completo'}),
            'cpf': forms.TextInput(attrs={'placeholder': '000.000.000-00'}),
            'email': forms.EmailInput(attrs={'placeholder': 'seu.email@exemplo.com'}),
        }

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if cpf:
            # Remove formatação
            cpf_limpo = re.sub(r'[^0-9]', '', cpf)
            
            # Valida o CPF
            if not validar_cpf(cpf_limpo):
                raise forms.ValidationError('CPF inválido. Por favor, digite um CPF válido.')
            
            # Retorna o CPF formatado
            return cpf_limpo
        return cpf

    def clean_password(self):
        return self.cleaned_data.get('password')
    
    # Sobrescreve o save para garantir que a senha seja tratada
    def save(self, commit=True):
        cliente = super().save(commit=False)
        if commit:
            cliente.save()
        return cliente


class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'placeholder': 'Seu email de cadastro'}),
        required=True
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={'placeholder': 'Digite sua senha'}),
        required=True
    )