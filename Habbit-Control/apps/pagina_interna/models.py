from datetime import date

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
    
    # Relacionamento com Cliente
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

    def save(self, *args, **kwargs):
        """Impede converter para negativo um hábito que ainda tem metas."""
        from django.core.exceptions import ValidationError

        if (
            self.pk
            and self.tipo_habito == 'negativo'
            and self.metas.exists()
        ):
            raise ValidationError('Exclua a meta antes de converter o hábito para negativo.')
        return super().save(*args, **kwargs)
    
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


class Meta(models.Model):
    """Objetivo único de quantidade para um hábito positivo do Cliente.

    A relação ``parceiros`` concede acesso de consulta às contas selecionadas;
    ela não transfere a propriedade nem as permissões de escrita do Cliente.
    """
    PERIODO_CHOICES = Habito.PERIODO_CHOICES

    habito = models.ForeignKey(Habito, on_delete=models.CASCADE, related_name='metas')
    quantidade_minima = models.PositiveIntegerField(verbose_name="Quantidade mínima")
    periodo = models.CharField(max_length=10, choices=PERIODO_CHOICES, verbose_name="Período")
    data_inicio = models.DateField(default=date.today, verbose_name="Início da meta")
    parceiros = models.ManyToManyField(
        'login_cadastro_app.Parceiro',
        blank=True,
        related_name='metas_partilhadas',
        verbose_name="Parceiros de acompanhamento",
    )
    streak = models.PositiveIntegerField(default=0, verbose_name="Sequência atual")
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Meta de {self.habito.nome_habito}: {self.quantidade_minima}/{self.get_periodo_display()}"

    class Meta:
        verbose_name = "Meta"
        verbose_name_plural = "Metas"
        ordering = ['-data_criacao']
        constraints = [
            models.UniqueConstraint(fields=['habito'], name='unique_goal_per_habit'),
        ]

    def clean(self):
        """Valida a regra de domínio que restringe metas a hábitos positivos."""
        from django.core.exceptions import ValidationError

        if self.habito_id and self.habito.tipo_habito != 'positivo':
            raise ValidationError({'habito': 'Metas só podem ser associadas a hábitos positivos.'})

    def save(self, *args, **kwargs):
        """Executa validação de domínio antes de persistir a meta."""
        self.full_clean()
        return super().save(*args, **kwargs)


class MetaCiclo(models.Model):
    """Resultado persistido de uma meta durante um período civil.

    ``progresso`` conserva a soma de atividades, ``estado`` regista o resultado
    e ``data_cumprimento`` marca a primeira vez em que o objetivo foi atingido
    dentro do ciclo.
    """
    ESTADO_ATIVA = 'ativa'
    ESTADO_CUMPRIDA = 'cumprida'
    ESTADO_NAO_CUMPRIDA = 'nao_cumprida'
    ESTADO_CHOICES = [
        (ESTADO_ATIVA, 'Ativa'),
        (ESTADO_CUMPRIDA, 'Cumprida'),
        (ESTADO_NAO_CUMPRIDA, 'Não cumprida'),
    ]

    meta = models.ForeignKey(Meta, on_delete=models.CASCADE, related_name='ciclos')
    inicio = models.DateField()
    fim = models.DateField()
    progresso = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=ESTADO_ATIVA)
    data_cumprimento = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Ciclo de Meta"
        verbose_name_plural = "Ciclos de Metas"
        ordering = ['inicio']
        constraints = [
            models.UniqueConstraint(fields=['meta', 'inicio'], name='unique_meta_cycle_start'),
        ]

    @property
    def percentual(self):
        """Retorna o progresso percentual limitado ao intervalo de 0 a 100."""
        if self.meta.quantidade_minima <= 0:
            return 0
        return min(100, round(self.progresso / self.meta.quantidade_minima * 100, 1))
