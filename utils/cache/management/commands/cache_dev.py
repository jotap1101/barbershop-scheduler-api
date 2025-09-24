"""
Django Management Command para gerenciar e testar cache Redis

Este comando fornece funcionalidades para:
- Testar conexão com cache
- Monitorar estatísticas
- Limpar cache por padrões
- Popular cache com dados de teste
- Verificar health check
"""

import json
import time
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

from utils.cache.cache_utils import CacheKeys, cache_manager


class Command(BaseCommand):
    help = "Utilitários para gerenciar e testar cache Redis"

    def add_arguments(self, parser):
        parser.add_argument(
            "--test-connection", action="store_true", help="Testa conexão com o cache"
        )

        parser.add_argument(
            "--stats", action="store_true", help="Mostra estatísticas do cache"
        )

        parser.add_argument(
            "--health-check", action="store_true", help="Verifica saúde do cache"
        )

        parser.add_argument(
            "--populate-test",
            action="store_true",
            help="Popula cache com dados de teste",
        )

        parser.add_argument(
            "--clear-all", action="store_true", help="Limpa todo o cache (CUIDADO!)"
        )

        parser.add_argument(
            "--clear-pattern",
            type=str,
            help="Limpa cache por padrão (ex: barbershop, service)",
        )

        parser.add_argument(
            "--list-keys",
            type=str,
            nargs="?",
            const="*",
            help="Lista chaves do cache (apenas Redis)",
        )

        parser.add_argument(
            "--monitor",
            action="store_true",
            help="Monitora operações de cache em tempo real",
        )

        parser.add_argument(
            "--backend-info",
            action="store_true",
            help="Mostra informações do backend de cache",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Barbershop Redis Cache Manager ==="))

        # Mostra informações do Redis
        self.stdout.write("🔧 Backend: Redis Cache")

        if options["test_connection"]:
            self.test_connection()
        elif options["stats"]:
            self.show_stats()
        elif options["health_check"]:
            self.health_check()
        elif options["populate_test"]:
            self.populate_test_data()
        elif options["clear_all"]:
            self.clear_all_cache()
        elif options["clear_pattern"]:
            self.clear_pattern(options["clear_pattern"])
        elif options["list_keys"]:
            self.list_keys(options["list_keys"])
        elif options["monitor"]:
            self.monitor_cache()
        elif options["backend_info"]:
            self.show_backend_info()
        else:
            self.stdout.write(
                self.style.WARNING("Use --help para ver as opções disponíveis")
            )

    def test_connection(self):
        """Testa conexão básica com o cache"""
        self.stdout.write(self.style.SUCCESS("🧪 Testando conexão com cache..."))

        try:
            # Teste básico
            test_key = "connection_test"
            test_data = {
                "timestamp": datetime.now().isoformat(),
                "message": "Cache connection test",
                "backend": cache_manager.get_backend_info()["backend"],
            }

            # Set/Get test
            cache.set(test_key, test_data, 30)
            retrieved = cache.get(test_key)

            if retrieved == test_data:
                self.stdout.write(
                    self.style.SUCCESS("✅ Cache funcionando corretamente!")
                )
                self.stdout.write(f"📦 Dados: {json.dumps(retrieved, indent=2)}")
            else:
                self.stdout.write(self.style.ERROR("❌ Falha no teste de cache"))

            # Limpar teste
            cache.delete(test_key)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro na conexão: {e}"))

    def show_stats(self):
        """Mostra estatísticas do cache"""
        self.stdout.write(self.style.SUCCESS("📊 Estatísticas do Cache"))

        try:
            stats = cache_manager.get_cache_stats()

            self.stdout.write(self.style.SUCCESS("\n=== Informações do Backend ==="))
            backend_info = stats["backend_info"]
            for key, value in backend_info.items():
                self.stdout.write(f"{key}: {value}")

            self.stdout.write(self.style.SUCCESS("\n=== Estatísticas por Tipo ==="))
            for key, value in stats.items():
                if key.endswith("_keys"):
                    pattern = key.replace("_keys", "")
                    self.stdout.write(f"🔑 {pattern}: {value} chaves")

            self.stdout.write(f"\n📈 Total de chaves: {stats.get('total_keys', 0)}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro ao obter estatísticas: {e}"))

    def health_check(self):
        """Verifica saúde do cache"""
        self.stdout.write(self.style.SUCCESS("🏥 Health Check do Cache"))

        is_healthy, message = cache_manager.health_check()

        if is_healthy:
            self.stdout.write(self.style.SUCCESS(f"✅ {message}"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ {message}"))

    def populate_test_data(self):
        """Popula cache com dados de teste"""
        self.stdout.write(
            self.style.SUCCESS("🌱 Populando cache com dados de teste...")
        )

        test_data = {
            f"{CacheKeys.BARBERSHOP_PREFIX}:test:1": {
                "id": 1,
                "name": "Barbearia Teste",
                "address": "Rua Teste, 123",
                "services_count": 5,
            },
            f"{CacheKeys.SERVICE_PREFIX}:test:1": {
                "id": 1,
                "name": "Corte Masculino",
                "price": 25.00,
                "duration": 30,
            },
            f"{CacheKeys.USER_PREFIX}:test:1": {
                "id": 1,
                "username": "joao_dev",
                "role": "BARBER",
                "is_active": True,
            },
            f"{CacheKeys.APPOINTMENT_PREFIX}:slots:today": [
                {"time": "09:00", "available": True},
                {"time": "10:00", "available": False},
                {"time": "11:00", "available": True},
            ],
            f"{CacheKeys.REVIEW_PREFIX}:summary": {
                "total_reviews": 150,
                "average_rating": 4.7,
                "five_star_count": 89,
            },
        }

        success_count = 0
        for key, data in test_data.items():
            try:
                cache.set(key, data, 300)  # 5 minutos TTL
                success_count += 1
                self.stdout.write(f"✅ Cached: {key}")
            except Exception as e:
                self.stdout.write(f"❌ Failed: {key} - {e}")

        self.stdout.write(
            self.style.SUCCESS(f"📦 {success_count}/{len(test_data)} entradas criadas")
        )

    def clear_all_cache(self):
        """Limpa todo o cache com confirmação"""
        self.stdout.write(
            self.style.WARNING("⚠️  ATENÇÃO: Isso vai limpar TODO o cache!")
        )

        confirm = input("Digite 'CONFIRMAR' para continuar: ")
        if confirm != "CONFIRMAR":
            self.stdout.write(self.style.SUCCESS("✅ Operação cancelada"))
            return

        try:
            cache.clear()
            self.stdout.write(self.style.SUCCESS("🧹 Cache limpo com sucesso!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro ao limpar cache: {e}"))

    def clear_pattern(self, pattern):
        """Limpa cache por padrão específico"""
        self.stdout.write(
            self.style.SUCCESS(f"🧹 Limpando cache com padrão: {pattern}")
        )

        try:
            removed_count = cache_manager.clear_pattern(pattern)

            if removed_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ {removed_count} entradas removidas")
                )
            else:
                self.stdout.write(
                    self.style.WARNING("⚠️  Nenhuma entrada encontrada para esse padrão")
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro ao limpar padrão: {e}"))

    def list_keys(self, pattern):
        """Lista chaves do cache Redis por padrão"""
        self.stdout.write(
            self.style.SUCCESS(f"🔍 Buscando chaves com padrão: {pattern}")
        )

        try:
            keys = cache_manager.get_keys_by_pattern(pattern)

            if keys:
                self.stdout.write(f"📋 Encontradas {len(keys)} chaves:")
                for key in keys[:20]:  # Limita a 20 para não sobrecarregar
                    self.stdout.write(f"  🔑 {key}")

                if len(keys) > 20:
                    self.stdout.write(f"... e mais {len(keys) - 20} chaves")
            else:
                self.stdout.write(self.style.WARNING("⚠️  Nenhuma chave encontrada"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erro ao listar chaves: {e}"))

    def monitor_cache(self):
        """Monitora operações de cache Redis em tempo real"""
        self.stdout.write(
            self.style.SUCCESS("👁️  Monitorando Redis cache (Ctrl+C para parar)...")
        )

        try:
            start_time = time.time()
            last_stats = cache_manager.get_cache_stats()

            while True:
                time.sleep(5)  # Check a cada 5 segundos

                current_stats = cache_manager.get_cache_stats()
                elapsed = int(time.time() - start_time)

                self.stdout.write(
                    f"\n⏱️  {elapsed}s - {datetime.now().strftime('%H:%M:%S')}"
                )

                backend_info = current_stats["backend_info"]
                self.stdout.write(
                    f"💾 Memória: {backend_info.get('used_memory', 'N/A')}"
                )
                self.stdout.write(
                    f"👥 Clientes: {backend_info.get('connected_clients', 'N/A')}"
                )
                self.stdout.write(f"🎯 Hit Rate: {backend_info.get('hit_rate', 'N/A')}")

                # Comparar com stats anteriores
                total_keys = current_stats.get("total_keys", 0)
                last_total = last_stats.get("total_keys", 0)
                key_diff = total_keys - last_total

                if key_diff != 0:
                    sign = "+" if key_diff > 0 else ""
                    self.stdout.write(f"🔑 Chaves: {total_keys} ({sign}{key_diff})")

                last_stats = current_stats

        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("\n✅ Monitoramento parado"))

    def show_backend_info(self):
        """Mostra informações detalhadas do backend"""
        self.stdout.write(self.style.SUCCESS("🔧 Informações do Redis Cache"))

        backend_info = cache_manager.get_backend_info()

        self.stdout.write(self.style.SUCCESS("\n=== Configuração ==="))
        for key, value in backend_info.items():
            if not key.startswith("keyspace") and key not in ["hit_rate"]:
                self.stdout.write(f"{key}: {value}")

        self.stdout.write(self.style.SUCCESS("\n=== Performance ==="))
        for key in ["hit_rate", "keyspace_hits", "keyspace_misses"]:
            if key in backend_info:
                self.stdout.write(f"{key}: {backend_info[key]}")

        # Configurações do Django
        self.stdout.write(self.style.SUCCESS("\n=== Configuração Django ==="))
        cache_config = settings.CACHES.get("default", {})
        self.stdout.write(f"Backend: {cache_config.get('BACKEND', 'N/A')}")
        self.stdout.write(f"Location: {cache_config.get('LOCATION', 'N/A')}")

        if "OPTIONS" in cache_config:
            self.stdout.write("Options:")
            for key, value in cache_config["OPTIONS"].items():
                self.stdout.write(f"  {key}: {value}")
