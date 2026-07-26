"""
Contador de Producao Nao-Intrusivo - Cenario LIGHT

Pinos (conforme diagram.json):
  - ldr1 (fotorresistor, saida AO) -> GPIO34 (ADC1_CH6)
  - btn1 (botao de reset)          -> GPIO4, PULL_UP interno, outra perna no GND

Polaridade do sensor (wokwi-photoresistor-sensor): o pino AO fica entre o LDR
(ligado ao GND) e um resistor fixo de 10K (ligado ao VCC). Por isso, MAIS luz
=> resistencia do LDR cai => MENOR leitura no ADC; MENOS luz (objeto bloqueando
o feixe) => MAIOR leitura no ADC. A logica abaixo respeita essa polaridade real
(confirmada na documentacao oficial do componente).
"""

from machine import Pin, ADC
import time

# ----------------------------- Hardware -------------------------------
PIN_LDR = 34
PIN_BOTAO = 4

ldr = ADC(Pin(PIN_LDR))
ldr.atten(ADC.ATTN_11DB)                       # habilita leitura em toda a faixa 0-3.3V

botao = Pin(PIN_BOTAO, Pin.IN, Pin.PULL_UP)    # solto = 1 | pressionado = 0

# ----------------------------- Parametros -------------------------------
# Leitura via read_u16() (escala fixa 0-65535, independente da resolucao do ADC).
# lux=800 (linha livre) -> ~12.4k | lux=50 (linha bloqueada) -> ~40.5k -> ampla margem.
LIMIAR_CLARO = 20000      # leitura ABAIXO disso = muita luz  -> linha livre  (>500 lux)
LIMIAR_ESCURO = 30000     # leitura ACIMA disso  = pouca luz  -> linha bloqueada (<100 lux)

TEMPO_MICROPARADA_MS = 5000    # tempo continuo bloqueado para caracterizar micro-parada
TEMPO_DEBOUNCE_MS = 50         # tempo de estabilizacao para validar o botao de reset

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

    leitura = ldr.read_u16()

    if estado_esteira == "LIVRE":
        if leitura > LIMIAR_ESCURO:                 # borda de descida: peca bloqueou a luz
            estado_esteira = "BLOQUEADO"
            inicio_bloqueio_ms = time.ticks_ms()
            alerta_emitido = False
    else:  # estado_esteira == "BLOQUEADO"
        if leitura < LIMIAR_CLARO:                   # borda de subida: peca passou por completo
            estado_esteira = "LIVRE"
            contador_pecas += 1
            print("Peca detectada! Total: {}".format(contador_pecas))
        elif not alerta_emitido:
            # Continua bloqueado: verifica tempo continuo sem variacao (timer nao-bloqueante)
            decorrido = time.ticks_diff(time.ticks_ms(), inicio_bloqueio_ms)
            if decorrido >= TEMPO_MICROPARADA_MS:
                print("Alerta: Micro-parada detectada!")
                alerta_emitido = True


def verifica_botao():
    """Le o botao de reset com debounce nao-bloqueante (baseado em timestamps).

    O reset e disparado na borda de SOLTURA (1) que sucede um pressionamento
    estavel (0) -- ou seja, ao final de um clique completo -- e nao no instante
    da pressao. Isso evita que a mensagem seja emitida enquanto o botao ainda
    esta sendo mantido pressionado, garantindo que ela ocorra apos o comando
    de soltura do cenario de teste (e nao antes dele).
    """
    global botao_anterior, botao_estavel, ultima_mudanca_botao_ms

    leitura_atual = botao.value()

    if leitura_atual != botao_anterior:
        botao_anterior = leitura_atual
        ultima_mudanca_botao_ms = time.ticks_ms()

    if time.ticks_diff(time.ticks_ms(), ultima_mudanca_botao_ms) > TEMPO_DEBOUNCE_MS:
        if leitura_atual != botao_estavel:
            estado_anterior_estavel = botao_estavel
            botao_estavel = leitura_atual
            if estado_anterior_estavel == 0 and botao_estavel == 1:  # pressionado -> solto
                reset_turno()


def main():
    print("Contador de Producao Inicializado")
    while True:
        verifica_sensor()
        verifica_botao()
        time.sleep_ms(20)   # pausa curta apenas para aliviar a CPU, nao compromete os testes


main()