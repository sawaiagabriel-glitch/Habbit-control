from django.core.management.base import BaseCommand

from apps.pagina_interna.models import Meta
from apps.pagina_interna.services import atualizar_ciclos_meta


class Command(BaseCommand):
    """Processa os ciclos de todas as metas sem duplicar fechamentos."""

    help = 'Atualiza o estado dos ciclos e as sequências das metas.'

    def handle(self, *args, **options):
        """Atualiza cada meta e informa quantas foram processadas."""
        metas_atualizadas = 0
        for meta in Meta.objects.select_related('habito').iterator():
            atualizar_ciclos_meta(meta)
            metas_atualizadas += 1

        self.stdout.write(
            self.style.SUCCESS(f'{metas_atualizadas} meta(s) atualizada(s).')
        )
