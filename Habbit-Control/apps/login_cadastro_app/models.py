from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Cliente(models.Model):
    
    # --- Dados Pessoais ---
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    idade = models.PositiveIntegerField(verbose_name="Idade")
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF")
    email = models.EmailField(unique=True, verbose_name="Email")
    
    # --- Senha do cliente (será armazenada como hash) ---
    password = models.CharField(max_length=128, verbose_name="Senha") # Máx length para hash SHA256
    
    # --- Localização ---
    estado = models.CharField(max_length=2, verbose_name="Estado", blank=True, null=True)
    cidade = models.CharField(max_length=100, verbose_name="Cidade", blank=True, null=True) 
    
    # --- Profissão ---
    profissao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Profissão")
    
    # --- Consentimentos ---
    lgpd = models.BooleanField(default=False, verbose_name="Aceitou Termos LGPD")
    
    # --- Metadata ---
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    
    def __str__(self):
        return f"{self.nome_completo} - {self.cpf}"

    # Método para verificar a senha
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    # Sobrescreve o save para hashear a senha se ela não estiver hasheada
    def save(self, *args, **kwargs):
        # Verifica se a senha não está hasheada
        if not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"