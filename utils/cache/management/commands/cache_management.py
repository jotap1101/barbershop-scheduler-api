"""
Comando de gerenciamento para operações de cache

Uso:
python manage.py cache_management --clear-all
python manage.py cache_management --stats
python manage.py cache_management --clear-pattern barbershop
"""

from django.core.management.base import BaseCommand, CommandError
from utils.cache.signals import manual_cache_invalidation, get_cache_stats
from utils.cache import cache_manager, CacheKeys


class Command(BaseCommand):
    help = "Gerencia o sistema de cache da aplicação"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear-all",
            action="store_true",
            help="Limpa todo o cache da aplicação",
        )

        parser.add_argument(
            "--stats",
            action="store_true",
            help="Mostra estatísticas do cache",
        )

        parser.add_argument(
            "--clear-pattern",
            type=str,
            help="Limpa cache de um padrão específico (barbershop, service, appointment, review, user)",
        )

        parser.add_argument(
            "--clear-specific",
            type=str,
            help="Limpa cache de um item específico (formato: model_name:id)",
        )

        parser.add_argument(
            "--warm-up",
            action="store_true",
            help="Aquece o cache com dados mais comuns",
        )

    def handle(self, *args, **options):
        if options["clear_all"]:
            self.clear_all_cache()

        elif options["stats"]:
            self.show_stats()

        elif options["clear_pattern"]:
            self.clear_pattern(options["clear_pattern"])

        elif options["clear_specific"]:
            self.clear_specific(options["clear_specific"])

        elif options["warm_up"]:
            self.warm_up_cache()

        else:
            self.stdout.write(
                self.style.WARNING(
                    "Nenhuma opção especificada. Use --help para ver as opções disponíveis."
                )
            )

    def clear_all_cache(self):
        """Limpa todo o cache"""
        try:
            result = manual_cache_invalidation()
            self.stdout.write(self.style.SUCCESS(f"✓ {result}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Erro ao limpar cache: {e}"))

    def show_stats(self):
        """Mostra estatísticas do cache"""
        try:
            stats = get_cache_stats()
            self.stdout.write(self.style.SUCCESS("📊 Estatísticas do Cache:"))

            for key, value in stats.items():
                if key == "status" and value == "active":
                    self.stdout.write(f"   {key}: {self.style.SUCCESS(value)}")
                elif key == "status" and value == "error":
                    self.stdout.write(f"   {key}: {self.style.ERROR(value)}")
                else:
                    self.stdout.write(f"   {key}: {value}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Erro ao obter estatísticas: {e}"))

    def clear_pattern(self, pattern):
        """Limpa cache de um padrão específico"""
        pattern_map = {
            "barbershop": CacheKeys.BARBERSHOP_PREFIX,
            "service": CacheKeys.SERVICE_PREFIX,
            "appointment": CacheKeys.APPOINTMENT_PREFIX,
            "review": CacheKeys.REVIEW_PREFIX,
            "user": CacheKeys.USER_PREFIX,
            "search": CacheKeys.SEARCH_PREFIX,
        }

        if pattern not in pattern_map:
            self.stdout.write(
                self.style.ERROR(
                    f"✗ Padrão inválido: {pattern}. "
                    f'Padrões válidos: {", ".join(pattern_map.keys())}'
                )
            )
            return

        try:
            cache_pattern = pattern_map[pattern]
            cache_manager.invalidate_pattern(cache_pattern)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Cache limpo para padrão: {pattern}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Erro ao limpar cache do padrão {pattern}: {e}")
            )

    def clear_specific(self, specific):
        """Limpa cache de um item específico"""
        try:
            if ":" not in specific:
                raise ValueError("Formato deve ser 'model_name:id'")

            model_name, item_id = specific.split(":", 1)
            item_id = int(item_id)

            cache_manager.invalidate_related_cache(model_name, item_id)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Cache limpo para {model_name} ID {item_id}")
            )

        except ValueError as e:
            self.stdout.write(self.style.ERROR(f"✗ Formato inválido: {e}"))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Erro ao limpar cache específico: {e}")
            )

    def warm_up_cache(self):
        """Aquece o cache com dados comuns (funcionalidade básica)"""
        self.stdout.write(self.style.SUCCESS("🔥 Aquecimento de cache iniciado..."))

        try:
            # Em um cenário real, aqui você faria requisições para endpoints importantes
            # Para demonstrar, vamos apenas informar que o aquecimento seria feito
            warm_up_actions = [
                "Carregando listagem de barbearias...",
                "Carregando serviços populares...",
                "Carregando horários disponíveis comuns...",
                "Carregando avaliações recentes...",
            ]

            for action in warm_up_actions:
                self.stdout.write(f"   {action}")

            self.stdout.write(
                self.style.SUCCESS(
                    "✓ Aquecimento de cache concluído! "
                    "(Em produção, isso faria requisições reais para popular o cache)"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Erro durante aquecimento: {e}"))
