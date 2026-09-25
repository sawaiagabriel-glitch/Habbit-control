from django.db import models
from apps.login_cadastro_app.models import Cliente

# Create your models here.

class Habito(models.Model):
    TIPO_CHOICES = [
        ('positivo', 'Positivo'),
        ('negativo', 'Negativo'),
    ]
    
    PERIODO_CHOICES = [
        ('dia', 'Dia'),
        ('semana', 'Semana'),
        ('mes', 'Mês'),
        ('ano', 'Ano'),
    ]
    
    # Relacionamento com Cliente através do CPF
    cliente = models.ForeignKey(
        Cliente, 
        on_delete=models.CASCADE, 
        related_name='habitos',
        verbose_name="Cliente"
    )
    
    # Tipo do hábito
    tipo_habito = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        verbose_name="Tipo do Hábito"
    )
    
    # Nome do hábito
    nome_habito = models.CharField(
        max_length=255,
        verbose_name="Nome do Hábito"
    )
    
    # Frequência atual
    frequencia_atual_valor = models.PositiveIntegerField(
        verbose_name="Frequência Atual (Valor)"
    )
    frequencia_atual_periodo = models.CharField(
        max_length=10,
        choices=PERIODO_CHOICES,
        verbose_name="Frequência Atual (Período)"
    )
    
    # Frequência desejada
    frequencia_desejada_valor = models.PositiveIntegerField(
        verbose_name="Frequência Desejada (Valor)"
    )
    frequencia_desejada_periodo = models.CharField(
        max_length=10,
        choices=PERIODO_CHOICES,
        verbose_name="Frequência Desejada (Período)"
    )
    
    # Metadata
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name="Data de Atualização"
    )
    
    def __str__(self):
        return f"{self.nome_habito} - {self.cliente.nome_completo}"
    
    class Meta:
        verbose_name = "Hábito"
        verbose_name_plural = "Hábitos"
        ordering = ['-data_criacao']


class RegistroAtividade(models.Model):  
    habito = models.ForeignKey(
        Habito,
        on_delete=models.CASCADE,
        related_name='registros',
        verbose_name="Hábito"
    )
    
    data = models.DateField(
        verbose_name="Data",
        auto_now_add=False
    )
    
    quantidade = models.PositiveIntegerField(
        default=1,
        verbose_name="Quantidade"
    )
    
    data_criacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    
    def __str__(self):
        return f"{self.habito.nome_habito} - {self.data} - {self.quantidade}x"
    
    class Meta:
        verbose_name = "Registro de Atividade"
        verbose_name_plural = "Registros de Atividades"
        ordering = ['-data', '-data_criacao']
        unique_together = ['habito', 'data']  # Um registro por hábito por dia
