#!/bin/bash

# Redis Development Management Script
# Autor: Barbershop Scheduler API
# Descrição: Script para gerenciar Redis no ambiente de desenvolvimento

COMPOSE_FILE="docker-compose.redis.yml"
CONTAINER_NAME="barbershop-redis-dev"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para imprimir mensagens coloridas
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Função para verificar se Docker está instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker não está instalado ou não está no PATH"
        exit 1
    fi
    
    # Verificar Docker Compose (v2 usa 'docker compose', v1 usa 'docker-compose')
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        print_error "Docker Compose não está instalado ou não está no PATH"
        exit 1
    fi
}

# Função para verificar se o Redis está rodando
is_redis_running() {
    docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"
}

# Função para iniciar Redis
start_redis() {
    print_status "Iniciando Redis para desenvolvimento..."
    
    if is_redis_running; then
        print_warning "Redis já está rodando!"
        return 0
    fi
    
        $COMPOSE_CMD -f $COMPOSE_FILE up -d
    
    # Aguardar Redis estar pronto
    print_info "Aguardando Redis inicializar..."
    sleep 3
    
    # Verificar se iniciou corretamente
    if is_redis_running; then
        print_status "✅ Redis iniciado com sucesso!"
        print_info "📍 Disponível em: localhost:6379"
        print_info "🐳 Container: $CONTAINER_NAME"
        
        # Testar conexão
        if docker exec $CONTAINER_NAME redis-cli ping &> /dev/null; then
            print_status "🔗 Conexão testada com sucesso"
        else
            print_warning "⚠️  Redis iniciou mas não responde ao ping"
        fi
    else
        print_error "❌ Falha ao iniciar Redis"
        return 1
    fi
}

# Função para parar Redis
stop_redis() {
    print_status "Parando Redis..."
    
    if ! is_redis_running; then
        print_warning "Redis não está rodando"
        return 0
    fi
    
    $COMPOSE_CMD -f $COMPOSE_FILE down
    print_status "✅ Redis parado com sucesso"
}

# Função para reiniciar Redis
restart_redis() {
    print_status "Reiniciando Redis..."
    stop_redis
    sleep 2
    start_redis
}

# Função para mostrar logs
show_logs() {
    if ! is_redis_running; then
        print_error "Redis não está rodando"
        return 1
    fi
    
    print_status "📋 Mostrando logs do Redis (Ctrl+C para sair)..."
    $COMPOSE_CMD -f $COMPOSE_FILE logs -f redis-dev
}

# Função para acessar CLI do Redis
redis_cli() {
    if ! is_redis_running; then
        print_error "Redis não está rodando"
        return 1
    fi
    
    print_status "🔧 Abrindo Redis CLI..."
    print_info "Comandos úteis: KEYS *, INFO, MONITOR, FLUSHALL"
    docker exec -it $CONTAINER_NAME redis-cli
}

# Função para mostrar status
show_status() {
    print_status "📊 Status do Redis:"
    echo
    
    if is_redis_running; then
        print_status "✅ Redis está RODANDO"
        
        # Informações do container
        echo -e "\n${BLUE}Container Info:${NC}"
        docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        
        # Informações do Redis
        echo -e "\n${BLUE}Redis Info:${NC}"
        if docker exec $CONTAINER_NAME redis-cli ping &> /dev/null; then
            docker exec $CONTAINER_NAME redis-cli INFO server | grep -E "redis_version|uptime_in_seconds|connected_clients"
            
            # Estatísticas de memória
            echo -e "\n${BLUE}Memory Usage:${NC}"
            docker exec $CONTAINER_NAME redis-cli INFO memory | grep -E "used_memory_human|maxmemory_human"
            
            # Número de chaves
            echo -e "\n${BLUE}Database Info:${NC}"
            key_count=$(docker exec $CONTAINER_NAME redis-cli DBSIZE)
            echo "Total keys: $key_count"
        else
            print_warning "Redis não responde aos comandos"
        fi
    else
        print_warning "❌ Redis NÃO está rodando"
    fi
}

# Função para limpeza completa
cleanup() {
    print_warning "🧹 Limpeza completa do Redis..."
    print_warning "Isso irá remover TODOS os dados do Redis!"
    
    read -p "Tem certeza? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $COMPOSE_CMD -f $COMPOSE_FILE down -v
        docker volume prune -f
        print_status "✅ Limpeza concluída"
    else
        print_info "Operação cancelada"
    fi
}

# Função para mostrar ajuda
show_help() {
    echo -e "${GREEN}Redis Development Management${NC}"
    echo -e "${BLUE}Usage:${NC} $0 [COMMAND]"
    echo
    echo -e "${YELLOW}Commands:${NC}"
    echo "  start     Inicia o Redis"
    echo "  stop      Para o Redis"
    echo "  restart   Reinicia o Redis"
    echo "  status    Mostra status e informações"
    echo "  logs      Mostra logs em tempo real"
    echo "  cli       Abre Redis CLI interativo"
    echo "  cleanup   Remove Redis e todos os dados"
    echo "  help      Mostra esta ajuda"
    echo
    echo -e "${YELLOW}Examples:${NC}"
    echo "  $0 start           # Inicia Redis"
    echo "  $0 status          # Verifica se está rodando"
    echo "  $0 cli             # Acessa Redis CLI"
}

# Verificar dependências
check_docker

# Processar comandos
case $1 in
    start)
        start_redis
        ;;
    stop)
        stop_redis
        ;;
    restart)
        restart_redis
        ;;
    logs)
        show_logs
        ;;
    cli)
        redis_cli
        ;;
    status)
        show_status
        ;;
    cleanup)
        cleanup
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        print_error "Nenhum comando especificado"
        echo
        show_help
        exit 1
        ;;
    *)
        print_error "Comando desconhecido: $1"
        echo
        show_help
        exit 1
        ;;
esac