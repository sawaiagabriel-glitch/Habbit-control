from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):
    # Sobrescreve o campo Senha para usar o Widget de Senha (oculta o texto)
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={'placeholder': 'Digite sua senha'}),
        max_length=100,
        required=True
    )
    lgpd = forms.BooleanField(
        label="Aceitou Termos LGPD",
        required=True,
        error_messages={'required': 'Este campo é obrigatório.'}
    )
    
    class Meta:
        model = Cliente
        fields = ['nome_completo', 'idade', 'email', 'password', 'estado', 'cidade', 'lgpd']
        
        widgets = {
            'nome_completo': forms.TextInput(attrs={'placeholder': 'Seu nome completo'}),
            'email': forms.EmailInput(attrs={'placeholder': 'seu.email@exemplo.com'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
            query = Cliente.objects.filter(email=email)
            if self.instance and self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise forms.ValidationError('Este email já está cadastrado. Por favor, use outro email ou faça login.')
        return email

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

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            return email.lower().strip()
        return email
