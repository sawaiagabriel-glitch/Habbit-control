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
        """Limita hábitos ao Cliente e exclui hábitos sem meta existente."""
        super().__init__(*args, **kwargs)
        self.cliente_id = cliente.id
        self.fields['habito'].queryset = Habito.objects.filter(
            cliente=cliente,
            tipo_habito='positivo',
        )
        self.fields['parceiros'].queryset = Parceiro.objects.order_by('nome_completo')

        if self.instance.pk is None:
            self.fields['habito'].queryset = self.fields['habito'].queryset.exclude(metas__isnull=False)

    def clean_quantidade_minima(self):
        """Rejeita objetivos nulos ou negativos antes de persistir a meta."""
        quantidade = self.cleaned_data['quantidade_minima']
        if quantidade < 1:
            raise forms.ValidationError('A quantidade mínima deve ser maior que zero.')
        return quantidade

    def clean_habito(self):
        """Garante que a meta use um hábito positivo ainda sem meta."""
        habito = self.cleaned_data['habito']
        if habito.tipo_habito != 'positivo':
            raise forms.ValidationError('Metas só podem ser associadas a hábitos positivos.')
        if self.instance.pk is None and habito.metas.exists():
            raise forms.ValidationError('Este hábito já possui uma meta.')
        return habito