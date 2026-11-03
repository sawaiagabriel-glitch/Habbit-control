from django import forms

from apps.login_cadastro_app.models import Parceiro
from .models import Habito, Meta


class MetaForm(forms.ModelForm):
    """Valida a criação de metas e as relações de partilha autorizadas."""
    parceiros = forms.ModelMultipleChoiceField(
        queryset=Parceiro.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Partilhar com parceiros',
    )

    class Meta:
        model = Meta
        fields = ['habito', 'quantidade_minima', 'periodo', 'parceiros']
        widgets = {
            'quantidade_minima': forms.NumberInput(attrs={'min': 1}),
        }

    def __init__(self, *args, cliente, **kwargs):
        """Limita o select aos hábitos positivos do Cliente ainda sem meta."""
        super().__init__(*args, **kwargs)
        self.cliente_id = cliente.id

        habitos_disponiveis = Habito.objects.filter(
            cliente=cliente,
            tipo_habito='positivo',
        )
        # Meta única por hábito: na criação, só entram hábitos sem meta.
        if self.instance.pk is None:
            habitos_disponiveis = habitos_disponiveis.filter(metas__isnull=True)

        self.fields['habito'].queryset = habitos_disponiveis
        self.fields['habito'].label_from_instance = lambda habito: habito.nome_habito
        self.fields['habito'].empty_label = 'Selecione um hábito'
        self.fields['parceiros'].queryset = Parceiro.objects.order_by('nome_completo')

    def clean_quantidade_minima(self):
        """Rejeita objetivos nulos ou negativos antes de persistir a meta."""
        quantidade = self.cleaned_data['quantidade_minima']
        if quantidade < 1:
            raise forms.ValidationError('A quantidade mínima deve ser maior que zero.')
        return quantidade

    def clean_habito(self):
        """Garante hábito do Cliente, positivo e ainda sem meta na criação."""
        habito = self.cleaned_data['habito']
        if habito.cliente_id != self.cliente_id:
            raise forms.ValidationError('Selecione um hábito da sua conta.')
        if habito.tipo_habito != 'positivo':
            raise forms.ValidationError('Metas só podem ser associadas a hábitos positivos.')
        if self.instance.pk is None and habito.metas.exists():
            raise forms.ValidationError('Este hábito já possui uma meta.')
        return habito