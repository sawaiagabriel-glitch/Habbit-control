from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Cliente(models.Model):
    
    # --- Dados Pessoais ---
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    idade = models.PositiveIntegerField(verbose_name="Idade")
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
        return f"{self.nome_completo} - {self.email}"

    # Método para verificar a senha
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    # Sobrescreve o save para hashear a senha se ela não estiver hasheada e normalizar o email
    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower().strip()
        # Verifica se a senha não está hasheada
        if not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


class Parceiro(models.Model):
    """Conta de leitura que recebe acesso apenas às metas partilhadas."""
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    email = models.EmailField(unique=True, verbose_name="Email")
    password = models.CharField(max_length=128, verbose_name="Senha")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")

    def __str__(self):
        return f"{self.nome_completo} - {self.email}"

    def check_password(self, raw_password):
        """Compara a senha informada com o hash guardado na conta."""
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        """Normaliza o email e guarda a senha sempre como hash Django."""
        self.email = self.email.lower().strip()
        if not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Parceiro de Acompanhamento"
        verbose_name_plural = "Parceiros de Acompanhamento"
