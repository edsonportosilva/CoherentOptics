import numpy as np
from utils import next_power_of_2, fft_convolution

def overlap_save_convolution(x, h, B, NFFT=None):
    """ Convolução Overlap-Save de x e h com comprimento de bloco B
        
        input:
            x (np.array): signal de entrada.
            h (np.array): coeficientes do filtro.
            B (int)     : comprimento do bloco.
            NFFT (int)  : comprimento do filtro.
        output:
            y np.array: sinal convoluído.
    """

    M = len(x)
    N = len(h)

    if NFFT is None:
        NFFT = max(B, next_power_of_2(N))
        
    # Determina o número de blocos de entrada
    num_input_blocks = np.ceil(M / B).astype(int) \
                     + np.ceil(NFFT / B).astype(int) - 1

    # realiza o zero padding ao sinal x para um múltiplo inteiro de B
    xp = np.pad(x, (0, num_input_blocks*B - M), mode='constant', constant_values=0+0j)

    output_size = num_input_blocks * B + N - 1
    y = np.zeros((output_size,), dtype="complex")
    
    # Buffer de entrada
    xw = np.zeros((NFFT,), dtype="complex")

    # Convolução de todos os blocos
    for n in range(num_input_blocks):
        # Extraia o enésimo bloco de entrada
        xb = xp[n*B:n*B+B]

        # Janela deslizante da entrada
        xw = np.roll(xw, -B)
        xw[-B:] = xb

        # Convolução rápida por FFT
        u = fft_convolution(xw, h)

        # Salve as amostras de saída válidas
        y[n*B:n*B+B] = u[-B:]

    y = y[:M+N-1]
    
    # Remove o atraso do filtro FIR
    start = (N - 1) // 2
    return y[start:start+M]

def lms(u, d, taps, mu):
    """ Least mean squares (LMS)
    
    Simples implementação do algoritmo LMS para filtragem adaptativa.

    Args:
        u (np.array): sinal de entrada unidimensional 
        d (np.array): sinal de referência unidimensional
        taps (int)  : número de coeficientes do filtro   
        mu (float)  : tamanho do passo para o LMS

    Returns:
        tuple: 
            - np.array: sinal de saída.
            - np.array: sinal de erro.
            - np.array: erro quadrático.
            - np.array: coeficintes do filtro após a convergência.
    """
    # número de iterações para filtragem adaptativa
    N = len(u) - taps + 1
    
    # deriva um filtro real ou complexo
    dtype = u.dtype
    
    # obtém o atraso da filtragem FIR
    dalay = (taps-1) // 2

    y = np.zeros(len(u), dtype=dtype)     # saída do filtro
    e = np.zeros(len(u), dtype=dtype)     # sinal de erro
    w = np.zeros(taps, dtype=dtype)       # coeficientes iniciais do filtro.

    err_square = np.zeros(len(u), dtype=dtype)   # erro quadrático
    
    # Execulta a filtragem adaptativa
    for n in range(N):
        
        # janela deslizante correspondente a ordem do filtro
        x = np.flipud(u[n:n+taps])

        # calcula a saída no instante n
        y[n] = np.dot(x, w)
        
        # calcula o erro
        e[n] = d[n + dalay] - y[n]
        
        # calcula os novos coeficientes do filtro
        w += mu * np.conj(x) * e[n]

        # calcula o erro quadrático
        err_square[n] = e[n]**2

    return y, e, err_square, w