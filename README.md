# Automação WhatsApp

Projeto em Python para automatizar rotinas comerciais no WhatsApp Web. A aplicação abre conversas, extrai mensagens recentes, registra conversas em webhooks do n8n, envia mensagens de follow-up e transcreve áudios recebidos usando `faster-whisper`.

## Visão geral

O projeto foi criado para apoiar o fluxo de atendimento e vendas, conectando conversas do WhatsApp com dados de negócios vindos de um CRM por meio do n8n.

Principais recursos:

- Abertura automática de conversas no WhatsApp Web por número de telefone.
- Leitura das últimas mensagens da conversa.
- Identificação de mensagens recebidas e enviadas.
- Registro de mensagens em webhooks do n8n.
- Registro de inconsistências, como telefone vazio ou contato não encontrado.
- Envio de mensagens para negócios perdidos.
- Follow-up manual assistido para negócios perdidos e abertos.
- Transcrição de mensagens de áudio usando captura de áudio do Windows e `faster-whisper`.
- Detecção básica de PDFs enviados na conversa.

## Tecnologias utilizadas

- Python 3
- Selenium
- Google Chrome com remote debugging
- WhatsApp Web
- n8n via webhooks HTTP
- faster-whisper
- pyaudiowpatch
- requests
- rich
- numpy

## Estrutura do projeto

```text
Automacao_whatsapp/
├── credentials/
│   └── .env
├── src/
│   ├── config.py
│   ├── extract_mensages.py
│   ├── send_menssage.py
│   ├── system_audio_transcribe.py
│   ├── training.py
│   └── util.py
├── LICENSE
└── README.md
```

## O que cada arquivo faz

### `src/config.py`

Configura e conecta o Selenium ao Google Chrome em modo debug.

Responsabilidades:

- Verificar se o Chrome já está aberto na porta de debug.
- Abrir o Chrome usando um perfil exclusivo para automação.
- Conectar o Selenium ao Chrome já aberto.
- Retornar o driver pronto para acessar o WhatsApp Web.

Configurações principais:

```python
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
USER_DATA_DIR = r"C:\ChromeBot"
DEBUG_PORT = 9222
```

### `src/extract_mensages.py`

Extrai mensagens da conversa aberta no WhatsApp Web.

Responsabilidades:

- Rolar a conversa até o topo.
- Ler até as últimas 100 mensagens carregadas.
- Ignorar mensagens já processadas, quando uma lista de IDs é informada.
- Identificar direção da mensagem: recebida, enviada ou desconhecida.
- Extrair data, autor e texto.
- Detectar PDFs.
- Detectar áudios e transcrever usando `faster-whisper`.
- Extrair a última mensagem enviada pelo usuário.

Funções principais:

```python
extract_recent_messages(driver, id_msg=None)
extract_last_mensage(driver)
conversation_to_string(messages)
```

### `src/system_audio_transcribe.py`

Faz a transcrição de áudios do WhatsApp.

Fluxo usado:

1. Identifica a duração exibida na bolha de áudio.
2. Dá play no áudio no WhatsApp Web.
3. Grava o áudio de saída do Windows usando WASAPI loopback.
4. Salva temporariamente um arquivo WAV.
5. Transcreve o arquivo com `faster-whisper`.
6. Remove o arquivo temporário.

Observação: essa parte depende do Windows e de suporte a WASAPI loopback.

### `src/training.py`

Script principal para extrair conversas de negócios abertos.

Fluxo geral:

1. Busca negócios abertos via webhook do n8n.
2. Abre o WhatsApp Web.
3. Para cada negócio, tenta abrir a conversa pelo telefone.
4. Extrai novas mensagens ainda não registradas.
5. Monta o payload com dados da mensagem e do CRM.
6. Envia as mensagens para o webhook de registro.
7. Registra inconsistências quando necessário.

Execução:

```bash
python src/training.py
```

### `src/send_menssage.py`

Script para envio de mensagens e follow-ups.

O menu atual permite:

1. Mandar mensagem para negócios perdidos.
2. Fazer follow-up de todos os negócios perdidos.
3. Fazer follow-up de negócios abertos.
4. Mandar mensagem para uma lista em CSV.

Execução:

```bash
python src/send_menssage.py
```

### `src/util.py`

Contém funções auxiliares e integrações com webhooks do n8n.

Responsabilidades:

- Buscar negócios por status.
- Importar dataset de mensagens.
- Registrar mensagens.
- Registrar inconsistências.
- Registrar tentativas de reativação de negócios perdidos.
- Buscar negócios perdidos.
- Normalizar números brasileiros com ou sem o nono dígito.
- Converter IDs de etapas do CRM para nomes legíveis.

## Requisitos

### Sistema operacional

O projeto foi desenvolvido com foco em Windows, principalmente por causa de:

- Caminho padrão do Chrome em `C:\Program Files\Google\Chrome\Application\chrome.exe`.
- Uso de WASAPI loopback para capturar áudio do sistema.
- Perfil dedicado do Chrome em `C:\ChromeBot`.

### Programas necessários

- Python 3.9 ou superior.
- Google Chrome instalado.
- Acesso ao WhatsApp Web.
- Conta do WhatsApp ativa para escanear o QR Code na primeira execução.
- Webhooks do n8n configurados.

### Dependências Python

O projeto não possui um arquivo `requirements.txt`. Com base nos imports, instale as dependências abaixo:

```bash
pip install selenium requests faster-whisper pyaudiowpatch numpy rich
```

Dependendo do ambiente, o Selenium também pode precisar do ChromeDriver compatível com a versão do Chrome. Em versões recentes do Selenium, o driver pode ser gerenciado automaticamente.

## Configuração inicial

### 1. Criar ambiente virtual

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Instalar dependências

```bash
pip install selenium requests faster-whisper pyaudiowpatch numpy rich
```

### 3. Conferir o caminho do Chrome

Abra `src/config.py` e confirme se o caminho abaixo existe na sua máquina:

```python
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
```

Caso o Chrome esteja em outro local, atualize a variável.

### 4. Criar a pasta do perfil da automação

O projeto usa um perfil separado do Chrome para manter a sessão do WhatsApp Web:

```text
C:\ChromeBot
```

Crie essa pasta manualmente ou altere o valor de `USER_DATA_DIR` em `src/config.py`.

### 5. Fazer login no WhatsApp Web

Na primeira execução, o Chrome será aberto em modo debug. Acesse o WhatsApp Web e escaneie o QR Code.

Depois disso, a sessão deve ficar salva no perfil `C:\ChromeBot`.

## Como executar

### Extrair mensagens de negócios abertos

```bash
python src/training.py
```

Esse comando busca negócios com status aberto, abre as conversas no WhatsApp e registra as mensagens encontradas no n8n.

### Enviar mensagens e follow-ups

```bash
python src/send_menssage.py
```

O script exibirá um menu interativo:

```text
1. Mandar mensagem para negócios perdidos
2. Fazer follow-up de todos os negócios perdidos
3. Fazer follow-up de negócios abertos
4. Mandar mensagem para uma lista
```

## Variáveis e configurações úteis

A transcrição de áudio usa duas variáveis opcionais de ambiente:

```bash
set WHISPER_MODEL_SIZE=base
set WHISPER_COMPUTE_TYPE=int8
```

Valores comuns para `WHISPER_MODEL_SIZE`:

- `tiny`
- `base`
- `small`
- `medium`
- `large-v3`

Quanto maior o modelo, melhor tende a ser a transcrição, mas maior será o consumo de memória e CPU.

## Integração com n8n

O arquivo `src/util.py` contém URLs de webhooks usados para:

- Buscar negócios.
- Buscar mensagens.
- Registrar novas mensagens.
- Registrar inconsistências.
- Registrar negócios perdidos.
- Buscar follow-ups.

Recomendação: mover essas URLs para variáveis de ambiente ou para um arquivo `.env` não versionado.

Exemplo sugerido:

```env
N8N_WEBHOOK_GET_DEALS=https://exemplo/webhook/get-deals
N8N_WEBHOOK_GET_MSGS=https://exemplo/webhook/get-msgs
N8N_WEBHOOK_ADD_MSG=https://exemplo/webhook/add-msg
N8N_WEBHOOK_ADD_INCONS=https://exemplo/webhook/add-inconsistencia
N8N_WEBHOOK_ADD_LOSTS=https://exemplo/webhook/add-losts
N8N_WEBHOOK_LOST_DEALS=https://exemplo/webhook/lost-deals
N8N_WEBHOOK_LOST_DEALS_FOLLOWUP=https://exemplo/webhook/lost-deals-followup
```

## Formato esperado dos dados

Os webhooks devem retornar objetos de negócio contendo campos usados pelo código, como:

```json
{
  "id_negocio": "123",
  "id_pessoa": "456",
  "title": "Nome do negócio",
  "name": "Nome do cliente",
  "phone": "11999999999",
  "stage_id": "1",
  "status": "aberto",
  "ids_msg": []
}
```

Para negócios perdidos, o código também espera campos como:

```json
{
  "mensage": "Texto da mensagem sugerida",
  "sugestao": "Sugestão de follow-up"
}
```

## Payload enviado para registro de mensagens

As mensagens são enviadas para o n8n com informações como:

```json
{
  "id": "ID da mensagem no WhatsApp",
  "mensagem": "Texto da mensagem",
  "timestamp_datahora_msg": "2026-01-01 10:00:00",
  "timestamp_datahora_lido": "2026-01-01 10:05:00",
  "numero_vendedor": "5511934072566",
  "numero_cliente": "11999999999",
  "mensagem_enviada_por": "Nome do remetente",
  "crm_negocio_etapa": "Qualificação",
  "crm_negocio_status": "aberto",
  "crm_negocio_id": 123,
  "crm_pessoa_id": 456
}
```

## Pontos de atenção

### Execução em outros sistemas operacionais

A automação de WhatsApp Web com Selenium pode funcionar em outros sistemas, mas a transcrição de áudio foi implementada para Windows. Em Linux ou macOS, será necessário adaptar a captura de áudio do sistema.

## Licença

Este projeto está sob a licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.
