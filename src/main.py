"""
Contador de Producao Nao-Intrusivo - Cenario LIGHT
Pinos assumidos:
  - ldr1 (fotorresistor, saida analogica) -> GPIO34 (ADC1_CH6)
  - btn1 (botao de reset, fio para GND)   -> GPIO4, com PULL_UP interno
"""

from machine import Pin, ADC
import time

# ----------------------------- Hardware -------------------------------
PIN_LDR = 34
PIN_BOTAO = 4

ldr = ADC(Pin(PIN_LDR))
ldr.atten(ADC.ATTN_11DB)                     # faixa de leitura: 0-3.3V (0-4095)

botao = Pin(PIN_BOTAO, Pin.IN, Pin.PULL_UP)   # solto = 1 | pressionado = 0

# ----------------------------- Parametros -------------------------------
LIMIAR_LIVRE = 2500        # leitura ADC acima disso => linha livre (muita luz)
LIMIAR_BLOQUEADO = 1500    # leitura ADC abaixo disso => linha bloqueada (pouca luz)
TEMPO_MICROPARADA_MS = 5000
TEMPO_DEBOUNCE_MS = 50

# --------------------------- Estado Global -------------------------------
contador_pecas = 0
estado_esteira = "LIVRE"          # "LIVRE" ou "BLOQUEADO"
inicio_bloqueio_ms = 0
alerta_emitido = False

botao_anterior = botao.value()
botao_estavel = botao_anterior
ultima_mudanca_botao_ms = time.ticks_ms()


def reset_turno():
    """Zera contadores e cronometros do turno atual."""
    global contador_pecas, estado_esteira, alerta_emitido
    contador_pecas = 0
    estado_esteira = "LIVRE"
    alerta_emitido = False
    print("Turno resetado com sucesso. Contadores zerados.")


def verifica_sensor():
    """Maquina de estados do LDR: conta pecas e detecta micro-paradas (nao-bloqueante)."""
    global estado_esteira, contador_pecas, inicio_bloqueio_ms, alerta_emitido

    leitura = ldr.read()

    if estado_esteira == "LIVRE":
        if leitura < LIMIAR_BLOQUEADO:             # borda de descida: peca chegou
            estado_esteira = "BLOQUEADO"
            inicio_bloqueio_ms = time.ticks_ms()
            alerta_emitido = False
    else:  # estado_esteira == "BLOQUEADO"
        if leitura > LIMIAR_LIVRE:                 # borda de subida: peca passou por completo
            estado_esteira = "LIVRE"
            contador_pecas += 1
            print("Peca detectada! Total: {}".format(contador_pecas))
        elif not alerta_emitido:
            # Ainda bloqueado: verifica tempo continuo sem variacao (timer nao-bloqueante)
            decorrido = time.ticks_diff(time.ticks_ms(), inicio_bloqueio_ms)
            if decorrido >= TEMPO_MICROPARADA_MS:
                print("Alerta: Micro-parada detectada!")
                alerta_emitido = True


def verifica_botao():
    """Le o botao de reset com debounce nao-bloqueante (baseado em timestamps)."""
    global botao_anterior, botao_estavel, ultima_mudanca_botao_ms

    leitura_atual = botao.value()

    if leitura_atual != botao_anterior:
        botao_anterior = leitura_atual
        ultima_mudanca_botao_ms = time.ticks_ms()

    if time.ticks_diff(time.ticks_ms(), ultima_mudanca_botao_ms) > TEMPO_DEBOUNCE_MS:
        if leitura_atual != botao_estavel:
            botao_estavel = leitura_atual
            if botao_estavel == 0:                 # nivel baixo estavel = botao pressionado
                reset_turno()


def main():
    print("Contador de Producao Inicializado")
    while True:
        verifica_sensor()
        verifica_botao()
        time.sleep_ms(20)   # pausa curta para aliviar a CPU


main()