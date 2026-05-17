# CaixaMonitor — Sistema de Monitoramento de Caixa d'Água com Arduino

> Trabalho de Engenharia de Software — Universidade de Vassouras  
> Disciplina: Engenharia de Software  
> Autor: Vinicius Gomes

---

## Sumário

1. [Visão Geral do Projeto](#visão-geral-do-projeto)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Componentes de Hardware](#componentes-de-hardware)
4. [Esquema de Ligação](#esquema-de-ligação)
5. [Firmware Arduino — Explicação do Código](#firmware-arduino--explicação-do-código)
6. [Script Python de Monitoramento — Explicação do Código](#script-python-de-monitoramento--explicação-do-código)
7. [Mockups da Interface Web (CaixaMonitor)](#mockups-da-interface-web-caixamonitor)
8. [Como Executar o Projeto](#como-executar-o-projeto)
9. [Dependências e Ferramentas](#dependências-e-ferramentas)
10. [Fluxo de Funcionamento](#fluxo-de-funcionamento)

---

## Visão Geral do Projeto

O **CaixaMonitor** é um sistema de monitoramento remoto do nível de caixa d'água utilizando um sensor ultrassônico conectado a um Arduino Uno. O sistema mede continuamente o nível de água e, por meio de um script Python em execução em um computador, envia alertas automáticos via **Telegram** quando o nível cai abaixo de limiares configurados.

O projeto é composto por três camadas:

| Camada | Tecnologia | Função |
|--------|-----------|--------|
| **Firmware embarcado** | Arduino Uno + C++ (PlatformIO) | Leitura do sensor ultrassônico e envio de dados pela porta serial |
| **Script de monitoramento** | Python 3 | Leitura serial, interpretação dos dados e disparo de alertas via Telegram |
| **Interface Web (protótipo)** | HTML/CSS/JS | Mockup completo da plataforma SaaS de visualização (CaixaMonitor) |

---

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        SISTEMA CAIXAMONITOR                     │
│                                                                 │
│  ┌──────────────┐   Serial (USB)   ┌──────────────────────────┐│
│  │              │ ───────────────► │                          ││
│  │  Arduino Uno │                  │   Script Python          ││
│  │  + HC-SR04   │                  │   (monitor.py)           ││
│  │              │ ◄─── 5V / GND ── │                          ││
│  └──────────────┘                  └────────────┬─────────────┘│
│                                                 │              │
│                                                 │ HTTPS        │
│                                                 ▼              │
│                                     ┌───────────────────────┐  │
│                                     │   API Telegram Bot    │  │
│                                     │  (alertas em tempo    │  │
│                                     │   real no celular)    │  │
│                                     └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

O Arduino realiza medições a cada 5 segundos e envia o percentual de nível pela porta serial. O Python lê esse valor, avalia se os limiares de alerta foram atingidos e dispara mensagens no Telegram.

---

## Componentes de Hardware

| Componente | Quantidade | Descrição |
|-----------|-----------|-----------|
| **Arduino Uno** | 1 | Microcontrolador principal (ATmega328P, 16 MHz) |
| **Sensor Ultrassônico HC-SR04** | 1 | Mede distância por ultrassom (2 cm a 400 cm, precisão ±3 mm) |
| **Cabos Jumper** | 4 | Conexão entre Arduino e sensor |
| **Protoboard** (opcional) | 1 | Auxílio na montagem |
| **Cabo USB Tipo-B** | 1 | Alimentação e comunicação serial com o computador |

### Sensor HC-SR04 — Princípio de Funcionamento

O HC-SR04 funciona emitindo um pulso ultrassônico de 40 kHz pelo pino **TRIG** e medindo o tempo que o eco leva para retornar ao pino **ECHO**. A distância é calculada pela fórmula:

```
Distância (cm) = Duração do pulso (µs) × velocidade do som (0,034 cm/µs) ÷ 2
```

O divisor por 2 existe porque o som percorre o trajeto de ida **e** volta.

---

## Esquema de Ligação

```
HC-SR04           Arduino Uno
─────────         ───────────
  VCC  ──────────  5V
  GND  ──────────  GND
  TRIG ──────────  Pino Digital 9
  ECHO ──────────  Pino Digital 10
```

**Importante:** O sensor deve ser fixado na **tampa** ou **borda superior** da caixa d'água, com o feixe ultrassônico apontado para baixo, em direção à superfície da água. A `ALTURA_CAIXA_CM` no código deve ser configurada com a distância real entre o sensor e o fundo da caixa quando ela estiver **vazia**.

---

## Firmware Arduino — Explicação do Código

**Arquivo:** [`src/main.cpp`](src/main.cpp)

```cpp
#include <Arduino.h>

const int trigPin = 9;
const int echoPin = 10;
const float ALTURA_CAIXA_CM = 100.0;
```

- **`trigPin = 9`**: pino de disparo do sensor — o Arduino envia um pulso HIGH por 10 µs para iniciar a medição.
- **`echoPin = 10`**: pino de eco — fica em HIGH durante o tempo que o som leva para ir e voltar.
- **`ALTURA_CAIXA_CM = 100.0`**: altura interna total da caixa em centímetros (distância do sensor até o fundo quando vazia). **Ajuste este valor** para a sua caixa.

---

```cpp
void setup() {
  Serial.begin(9600);
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}
```

- **`Serial.begin(9600)`**: inicializa a comunicação serial a 9600 baud — mesma taxa que o Python usa para ler os dados.
- **`pinMode(trigPin, OUTPUT)`**: configura o pino TRIG como saída (o Arduino envia o pulso).
- **`pinMode(echoPin, INPUT)`**: configura o pino ECHO como entrada (o Arduino recebe o sinal de retorno).

---

```cpp
void loop() {
  // ── PASSO 1: gera o pulso de disparo ──
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
```

O protocolo do HC-SR04 exige uma sequência precisa:
1. Baixar o TRIG para LOW por 2 µs (garantir estado limpo).
2. Elevar para HIGH por exatamente **10 µs** (dispara o pulso ultrassônico).
3. Baixar novamente para LOW (finaliza o disparo).

---

```cpp
  // ── PASSO 2: mede a duração do eco ──
  long duracao = pulseIn(echoPin, HIGH);
```

- **`pulseIn(echoPin, HIGH)`**: aguarda o pino ECHO ficar HIGH e mede por quantos **microssegundos** ele permanece assim. Esse tempo representa a viagem de ida e volta do som.

---

```cpp
  // ── PASSO 3: converte para distância e nível ──
  float distancia = duracao * 0.034 / 2;
  float nivel = ALTURA_CAIXA_CM - distancia;
  float porcentagem = constrain((nivel / ALTURA_CAIXA_CM) * 100, 0, 100);
```

| Variável | Cálculo | Significado |
|---------|---------|-------------|
| `distancia` | `duração × 0,034 ÷ 2` | Distância em cm do sensor até a superfície da água |
| `nivel` | `ALTURA_CAIXA_CM − distancia` | Altura real da coluna de água em cm |
| `porcentagem` | `(nivel ÷ ALTURA_CAIXA_CM) × 100` | Percentual de preenchimento da caixa |

- **`constrain(..., 0, 100)`**: limita o valor entre 0% e 100%, evitando leituras inválidas (por ex. quando a caixa está completamente cheia e o eco reflete imediatamente).

**Exemplo prático:**
- Caixa de 100 cm, sensor mede 30 cm até a água → `nivel = 100 − 30 = 70 cm` → `70%`

---

```cpp
  // ── PASSO 4: envia pela serial ──
  Serial.print("NIVEL:");
  Serial.println(porcentagem);

  delay(5000);
}
```

- O dado é enviado no formato `NIVEL:72.34` — prefixo fixo `NIVEL:` para que o Python identifique e ignore outras mensagens de debug.
- **`delay(5000)`**: aguarda 5 segundos antes da próxima medição. Pode ser reduzido para leituras mais frequentes.

---

## Script Python de Monitoramento — Explicação do Código

**Arquivo:** [`monitor.py`](monitor.py)

```python
import serial
import requests
import time
```

- **`serial`**: biblioteca PySerial — lê os dados enviados pelo Arduino pela porta USB/serial.
- **`requests`**: faz requisições HTTP para a API do Telegram.
- **`time`**: controla o intervalo de cooldown entre alertas.

---

```python
PORTA_SERIAL = 'COM3'
BAUD_RATE = 9600
TELEGRAM_TOKEN = 'SEU_TOKEN_AQUI'
TELEGRAM_CHAT_ID = 'SEU_CHAT_ID_AQUI'
NIVEL_MINIMO = 20
NIVEL_CRITICO = 10
```

| Variável | Descrição |
|---------|-----------|
| `PORTA_SERIAL` | Porta onde o Arduino está conectado (Windows: `COM3`, Linux: `/dev/ttyUSB0`) |
| `BAUD_RATE` | Taxa de comunicação — deve ser idêntica ao `Serial.begin()` do Arduino |
| `TELEGRAM_TOKEN` | Token do bot do Telegram (obtido via @BotFather) |
| `TELEGRAM_CHAT_ID` | ID do chat/grupo que receberá os alertas |
| `NIVEL_MINIMO` | Limiar de aviso (⚠️) — padrão 20% |
| `NIVEL_CRITICO` | Limiar crítico (🚨) — padrão 10% |

---

```python
def enviar_telegram(mensagem):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'text': mensagem})
```

Envia uma mensagem de texto para o bot do Telegram via requisição HTTP POST. A URL segue o padrão da API pública do Telegram (`sendMessage`).

---

```python
def monitorar():
    ser = serial.Serial(PORTA_SERIAL, BAUD_RATE, timeout=10)
    print("Monitorando caixa d'água...")
    ultimo_alerta = 0

    while True:
        linha = ser.readline().decode('utf-8').strip()
        if linha.startswith('NIVEL:'):
            nivel = float(linha.replace('NIVEL:', ''))
            print(f'Nível atual: {nivel:.1f}%')

            agora = time.time()
            if nivel <= NIVEL_CRITICO and agora - ultimo_alerta > 3600:
                enviar_telegram(f'🚨 ALERTA CRÍTICO! Caixa d\'água com apenas {nivel:.1f}%!')
                ultimo_alerta = agora
            elif nivel <= NIVEL_MINIMO and agora - ultimo_alerta > 3600:
                enviar_telegram(f'⚠️ Atenção! Nível da caixa baixo: {nivel:.1f}%')
                ultimo_alerta = agora
```

**Lógica de funcionamento:**

1. **`serial.Serial(..., timeout=10)`**: abre a porta serial com timeout de 10 segundos por leitura.
2. **`ser.readline()`**: aguarda uma linha completa (`\n`) do Arduino.
3. **`decode('utf-8').strip()`**: converte bytes para string e remove espaços/quebras de linha.
4. **`startswith('NIVEL:')`**: filtra apenas as linhas com dados de nível.
5. **`float(linha.replace('NIVEL:', ''))`**: extrai o valor numérico do percentual.
6. **`agora - ultimo_alerta > 3600`**: **cooldown de 1 hora** — evita spam de alertas, enviando no máximo 1 mensagem por hora.
7. A verificação do crítico (≤ 10%) tem **prioridade** sobre o aviso (≤ 20%) por estar no `if` antes do `elif`.

---

## Mockups da Interface Web (CaixaMonitor)

**Arquivo:** [`web/mockups.html`](web/mockups.html)

O protótipo visual da plataforma **CaixaMonitor** foi desenvolvido em HTML/CSS/JS puro e apresenta 6 telas funcionais:

### Tela 1 — Login / Cadastro
Tela de autenticação com alternância entre "Entrar" e "Criar conta", com campos de e-mail e senha.

### Tela 2 — Dashboard Principal
Visão geral de todas as caixas monitoradas. Exibe:
- Cards de estatísticas (total de caixas, alertas ativos, dispositivos offline)
- Lista de dispositivos com barra de nível, percentual e status (Online/Offline/Crítico)

### Tela 3 — Detalhe do Dispositivo
Tela dedicada a uma caixa específica com:
- **Gauge circular** mostrando o percentual atual (72%)
- Estimativa de duração do estoque de água
- Gráfico histórico do nível (últimas 24h / 7 dias / 30 dias)
- Histórico de alertas disparados com canais de notificação

### Tela 4 — Regras de Alerta
Gerenciamento das regras configuráveis por dispositivo:
- Condição (abaixo/acima de X%)
- Severidade (Info / Aviso / Crítica)
- Cooldown entre alertas
- Canais de notificação (Telegram, WhatsApp)
- Ativar/desativar via toggle

### Tela 5 — Configurações
- Gerenciamento de organização e URL única
- Membros da equipe com papéis (Admin / Operator / Viewer)
- Planos: FREE / CASA (R$ 19/mês) / PRO (R$ 49/mês)

### Tela 6 — Modal: Nova Regra de Alerta
Formulário para criação de nova regra de alerta com todos os campos configuráveis.

---

## Como Executar o Projeto

### Pré-requisitos
- Arduino Uno com PlatformIO (VS Code + extensão PlatformIO IDE)
- Python 3.8 ou superior
- Conta no Telegram + bot criado via @BotFather

### 1. Gravar o firmware no Arduino

```bash
# Na pasta do projeto PlatformIO:
pio run --target upload
```

Ou use o botão **Upload** (→) na interface do PlatformIO IDE.

### 2. Configurar o script Python

Edite o arquivo `monitor.py` e preencha as variáveis:

```python
PORTA_SERIAL = 'COM3'          # verifique no Gerenciador de Dispositivos
TELEGRAM_TOKEN = 'xxxx:yyyy'   # token do @BotFather
TELEGRAM_CHAT_ID = '123456789' # ID do seu chat
NIVEL_MINIMO = 20              # % para alerta de aviso
NIVEL_CRITICO = 10             # % para alerta crítico
```

Também ajuste a constante no Arduino caso sua caixa tenha altura diferente de 100 cm:

```cpp
// src/main.cpp
const float ALTURA_CAIXA_CM = 150.0; // exemplo: caixa de 150 cm
```

### 3. Instalar dependências Python

```bash
pip install pyserial requests
```

### 4. Executar o monitoramento

```bash
python monitor.py
```

O terminal exibirá o nível atual a cada 5 segundos e enviará alertas no Telegram quando necessário.

### 5. Visualizar os mockups

Abra o arquivo `web/mockups.html` diretamente no navegador — não requer servidor web.

---

## Dependências e Ferramentas

### Firmware (Arduino)
| Dependência | Versão | Descrição |
|------------|--------|-----------|
| PlatformIO | ≥ 6.x | Build system e upload |
| platform: atmelavr | latest | Suporte ao ATmega328P |
| framework: arduino | latest | Framework Arduino |

### Python
| Dependência | Versão | Instalação |
|------------|--------|-----------|
| pyserial | ≥ 3.5 | `pip install pyserial` |
| requests | ≥ 2.28 | `pip install requests` |

### Web (mockups)
Sem dependências externas — HTML/CSS/JS puro, funciona offline.

---

## Fluxo de Funcionamento

```
┌──────────────────────────────────────────────────────┐
│                   CICLO DE MEDIÇÃO (5s)              │
│                                                      │
│  Arduino envia pulso TRIG (10µs)                    │
│         ↓                                           │
│  HC-SR04 emite ultrassom (40kHz)                    │
│         ↓                                           │
│  ECHO fica HIGH pelo tempo de ida e volta           │
│         ↓                                           │
│  Arduino calcula: distancia → nivel → porcentagem   │
│         ↓                                           │
│  Envia "NIVEL:XX.X\n" pela serial                   │
│         ↓                                           │
│  Python lê a linha e extrai o valor                 │
│         ↓                                           │
│  nível ≤ 10%? → Alerta CRÍTICO via Telegram 🚨      │
│  nível ≤ 20%? → Alerta de AVISO via Telegram ⚠️     │
│  nível > 20%? → Apenas log no terminal              │
└──────────────────────────────────────────────────────┘
```

---

## Licença

Este projeto é de uso acadêmico — Universidade de Vassouras, 2025.
