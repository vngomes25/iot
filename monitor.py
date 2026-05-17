import serial
import requests
import time

# ===== CONFIGURAÇÕES — preenche aqui =====
PORTA_SERIAL = 'COM3'        # mesma porta do Arduino
BAUD_RATE = 9600
TELEGRAM_TOKEN = 'SEU_TOKEN_AQUI'
TELEGRAM_CHAT_ID = 'SEU_CHAT_ID_AQUI'
NIVEL_MINIMO = 20            # alerta quando abaixo de 20%
NIVEL_CRITICO = 10           # alerta crítico abaixo de 10%
# =========================================

def enviar_telegram(mensagem):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    requests.post(url, data={'chat_id': TELEGRAM_CHAT_ID, 'text': mensagem})

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

if __name__ == '__main__':
    monitorar()