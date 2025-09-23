# Logs Directory

Este diretório contém os arquivos de log do sistema:

## Arquivos de Log:

- **api_usage.log**: Registra todas as requisições da API com métricas detalhadas
- **api_errors.log**: Registra erros e exceções das APIs
- **django.log**: Logs gerais do Django

## Rotação de Logs:

- api_usage.log: 50MB por arquivo, 10 arquivos de backup
- api_errors.log: 10MB por arquivo, 5 arquivos de backup
- django.log: 10MB por arquivo, 5 arquivos de backup

## Formato dos Logs:

### API Usage (JSON):

```json
{
  "type": "API_REQUEST",
  "timestamp": "2025-09-23T10:30:45",
  "method": "POST",
  "path": "/api/appointment/",
  "status_code": 201,
  "duration": 0.342,
  "user": "john_doe#123",
  "client_ip": "192.168.1.100",
  "endpoint_category": "appointment"
}
```

### API Errors:

```
2025-09-23 10:30:45 - ERROR - API_ERROR: POST /api/payment/ returned 400
```
