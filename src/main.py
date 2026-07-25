import time
from machine import Pin, ADC

# Configuração dos Pinos (Ajuste os números dos pinos se o seu diagram.json usar outros)
PINO_LDR = 34       # Entrada analógica do sensor de luz
PINO_BOTAO = 12     # Entrada digital do botão de zerar/reset
PINO_LED = 2        # Saída do LED de status/alerta

# Inicialização dos Periféricos
ldr = ADC(Pin(PINO_LDR))
ldr.atten(ADC.ATTN_11DB)  # Configura leitura de 0V a 3.3V

botao = Pin(PINO_BOTAO, Pin.IN, Pin.PULL_UP)
led = Pin(PINO_LED, Pin.OUT)

# Mensagem inicial esperada pela esteira de testes
print("Contador de Producao Inicializado")

# Variáveis do sistema
contador = 0
estado_ldr_anterior = False
tempo_anterior_check = time.ticks_ms()

# Limiar de detecção da peça (ajuste conforme o valor do seu LDR)
LIMIAR_LUZ = 2000

while True:
    tempo_atual = time.ticks_ms()
    
    # 1. Leitura do Botão (Reset sem usar sleep)
    if botao.value() == 0:
        if contador != 0:
            contador = 0
            print("Contador zerado pelo botao.")

    # 2. Leitura do LDR com verificação em pequenos intervalos de tempo
    if time.ticks_diff(tempo_atual, tempo_anterior_check) >= 50:
        tempo_anterior_check = tempo_atual
        
        valor_ldr = ldr.read()
        peca_presente = valor_ldr < LIMIAR_LUZ
        
        # Transição: a peça acabou de passar na frente do sensor
        if peca_presente and not estado_ldr_anterior:
            contador += 1
            print(f"Peca detectada! Total: {contador}")
            led.on()
        elif not peca_presente and estado_ldr_anterior:
            led.off()
            
        estado_ldr_anterior = peca_presente