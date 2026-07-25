import time
from machine import Pin, ADC

# Configuração dos Pinos (LDR = GPIO34, Botão = GPIO4)
PIN_LDR = 34
PIN_BOTAO = 4

ldr = ADC(Pin(PIN_LDR))
ldr.atten(ADC.ATTN_11DB)

botao = Pin(PIN_BOTAO, Pin.IN, Pin.PULL_UP)

print("Contador de Producao Inicializado")

LIMIAR_BLOQUEADO = 1500
LIMIAR_LIVRE = 2500
TEMPO_MICROPARADA_MS = 5000

contador_pecas = 0
estado_esteira = "LIVRE"
inicio_bloqueio_ms = 0
alerta_emitido = False

# Trava para o botão não imprimir milhares de vezes
botao_pressionado_anterior = False

while True:
    t_atual = time.ticks_ms()
    
    # --- 1. LÓGICA DO BOTÃO (Trava para imprimir APENAS UMA VEZ no clique) ---
    botao_pressionado = (botao.value() == 0)
    
    if botao_pressionado and not botao_pressionado_anterior:
        contador_pecas = 0
        estado_esteira = "LIVRE"
        alerta_emitido = False
        print("Turno resetado com sucesso. Contadores zerados.")
        
    botao_pressionado_anterior = botao_pressionado

    # --- 2. LÓGICA DO SENSOR LDR (Máquina de Estados) ---
    leitura = ldr.read()

    if estado_esteira == "LIVRE":
        if leitura < LIMIAR_BLOQUEADO:
            estado_esteira = "BLOQUEADO"
            inicio_bloqueio_ms = t_atual
            alerta_emitido = False
    
    elif estado_esteira == "BLOQUEADO":
        if leitura > LIMIAR_LIVRE:
            estado_esteira = "LIVRE"
            contador_pecas += 1
            print("Peca detectada! Total: {}".format(contador_pecas))
        elif not alerta_emitido:
            if time.ticks_diff(t_atual, inicio_bloqueio_ms) >= TEMPO_MICROPARADA_MS:
                print("Alerta: Micro-parada detectada!")
                alerta_emitido = True