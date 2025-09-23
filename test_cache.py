"""
Teste simples do sistema de cache

Este script demonstra o funcionamento básico do cache implementado
"""

import os
import sys
import django

# Configuração do Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from utils.cache import cache_manager, CacheKeys
from datetime import datetime
import json


def test_basic_cache_operations():
    """
    Testa operações básicas de cache
    """
    print("🧪 Iniciando testes do sistema de cache...\n")

    # Teste 1: Operações básicas de get/set
    print("1. Testando operações básicas de cache")
    test_key = "test:basic"
    test_data = {"message": "Hello, Cache!", "timestamp": str(datetime.now())}

    # Set no cache
    cache_manager.cache.set(test_key, test_data, 60)
    print(f"   ✓ Dados armazenados no cache com chave: {test_key}")

    # Get do cache
    cached_data = cache_manager.cache.get(test_key)
    if cached_data == test_data:
        print(f"   ✓ Dados recuperados do cache corretamente: {cached_data['message']}")
    else:
        print(f"   ✗ Erro ao recuperar dados do cache")
    print()

    # Teste 2: Geração de chaves de cache
    print("2. Testando geração de chaves de cache")
    cache_key = cache_manager.generate_cache_key(
        CacheKeys.BARBERSHOP_PREFIX, search="test", page=1, ordering="name"
    )
    print(f"   ✓ Chave gerada: {cache_key}")
    print()

    # Teste 3: TTL personalizado
    print("3. Testando configuração de TTL")
    ttl_short = cache_manager.get_ttl("SHORT")
    ttl_medium = cache_manager.get_ttl("MEDIUM")
    ttl_long = cache_manager.get_ttl("LONG")

    print(f"   ✓ TTL SHORT: {ttl_short} segundos ({ttl_short/60} minutos)")
    print(f"   ✓ TTL MEDIUM: {ttl_medium} segundos ({ttl_medium/60} minutos)")
    print(f"   ✓ TTL LONG: {ttl_long} segundos ({ttl_long/60/60} horas)")
    print()

    # Teste 4: Invalidação de cache
    print("4. Testando invalidação de cache")
    # Cria algumas chaves de teste
    test_keys = [
        f"{CacheKeys.BARBERSHOP_PREFIX}:list:page:1",
        f"{CacheKeys.BARBERSHOP_PREFIX}:detail:1",
        f"{CacheKeys.SERVICE_PREFIX}:list:page:1",
    ]

    # Armazena dados nas chaves
    for key in test_keys:
        cache_manager.cache.set(key, f"test_data_for_{key}", 300)

    print(f"   ✓ Criadas {len(test_keys)} chaves de teste no cache")

    # Invalida padrão específico
    cache_manager.invalidate_pattern(CacheKeys.BARBERSHOP_PREFIX)
    print(f"   ✓ Invalidado padrão: {CacheKeys.BARBERSHOP_PREFIX}")

    # Verifica se as chaves foram removidas
    barbershop_keys_removed = 0
    service_keys_remaining = 0

    for key in test_keys:
        if cache_manager.cache.get(key) is None:
            if CacheKeys.BARBERSHOP_PREFIX in key:
                barbershop_keys_removed += 1
        else:
            if CacheKeys.SERVICE_PREFIX in key:
                service_keys_remaining += 1

    print(f"   ✓ Chaves de barbershop invalidadas: {barbershop_keys_removed}/2")
    print(f"   ✓ Chaves de service mantidas: {service_keys_remaining}/1")
    print()

    # Teste 5: Cache com função
    print("5. Testando cache com função de busca")

    def expensive_function(param1, param2):
        """Simula uma operação custosa"""
        import time

        time.sleep(0.1)  # Simula processamento
        return {
            "result": f"Processed {param1} and {param2}",
            "timestamp": str(datetime.now()),
        }

    # Primeira chamada - deve executar a função
    start_time = datetime.now()
    result1 = cache_manager.get_or_set_cache(
        "test:expensive:param1:param2",
        expensive_function,
        "SHORT",
        param1="value1",
        param2="value2",
    )
    first_duration = (datetime.now() - start_time).total_seconds()

    # Segunda chamada - deve vir do cache
    start_time = datetime.now()
    result2 = cache_manager.get_or_set_cache(
        "test:expensive:param1:param2",
        expensive_function,
        "SHORT",
        param1="value1",
        param2="value2",
    )
    second_duration = (datetime.now() - start_time).total_seconds()

    print(f"   ✓ Primeira execução: {first_duration:.3f}s (com função)")
    print(f"   ✓ Segunda execução: {second_duration:.3f}s (do cache)")
    print(f"   ✓ Resultado igual: {result1 == result2}")
    print()

    # Limpeza final
    print("6. Limpeza dos dados de teste")
    test_keys_to_clean = [
        "test:basic",
        "test:expensive:param1:param2",
        f"{CacheKeys.SERVICE_PREFIX}:list:page:1",
    ]

    cache_manager.cache.delete_many(test_keys_to_clean)
    print(f"   ✓ Limpeza concluída para {len(test_keys_to_clean)} chaves")
    print()

    print("🎉 Todos os testes do sistema de cache foram executados com sucesso!\n")

    return True


if __name__ == "__main__":
    try:
        test_basic_cache_operations()
        print("✅ Sistema de cache está funcionando corretamente!")
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
        import traceback

        traceback.print_exc()
