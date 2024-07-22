import numpy as np
from utils import plot4thPower
import matplotlib.pyplot as plt

def fourthPower(sigRx, Fs, plotSpectrum=False):
    """
    Compensa o deslocamento de frequência utilizando o método
    de quarta potência.

    Parameters
    ----------
    sigRx : np.array
        Sinal a ser compensado.

    Fs : int
        taxa de amostragem.

    plotSpectrum : bool, optional
        Retorna o espectro do sinal em quarta potência, by default False

    Returns
    -------
    tuple
        - sigRx (np.array): Sinal compensado.
        - indFO (float): Estimativa do deslocamento de frequência.
    
    Referências
    -----------
    [1] Digital Coherent Optical Systems, Architecture and Algorithms
    """
    
    try:
        nModes = sigRx.shape[1]
    except IndexError:
        sigRx = sigRx.reshape(len(sigRx), 1)
    
    NFFT     = sigRx.shape[0]
    axisFreq = Fs * np.fft.fftfreq(NFFT)
    
    time = np.arange(0, sigRx.shape[0]) * 1/Fs

    for indMode in range(nModes):
        
        # Elevar a quarta potência e aplica a FFT
        fourth_power = np.fft.fft(sigRx[:, indMode]**4)

        # Inferir o índice de valor máximo na frequência
        indFO = np.argmax(np.abs(fourth_power))
        
        # Obtenha a estimativa do deslocamento de frequência
        indFO = axisFreq[indFO]/4       
        
        # Compense o deslocamento de frequência
        sigRx[:, indMode] *= np.exp(-1j * 2 * np.pi * indFO * time)
    
    # Plote o espectro da quarta potência de um dos modos.
    if plotSpectrum:
        plot4thPower(sigRx, axisFreq)
        
    return sigRx, indFO

def movingAverage(x, N, alpha=0.03, window='constant'):
    """
    Calcula a média móvel para um array 2D ao longo de cada coluna.

    Parameters
    ----------
    x : np.array
        Matriz 2D do tipo (M,N), onde M é a quantidade das amostras
        e N o número de colunas.

    N : int
        Comprimento da janela.

    alpha : float, optional
        Parâmetro de escala (dispersão da distribuição laplaciana), by default 0.03

    window : str, optional
        Define a janela da média móvel [constant, laplacian], by default 'constant'

    Returns
    -------
    np.array
        Matriz 2D contendo a média móvel ao longo de cada coluna.
    
    Raises
    ------
    ValueError
        Caso a janela não seja especificada de forma correta.
    """
    
    nModes = x.shape[1]

    if window == 'constant':
        h = np.ones(N) / N
    
    elif window == 'laplacian':
        w = np.arange(-N // 2, N // 2)
        h = np.exp(-np.abs(w)*alpha)
    
    else:
        raise ValueError('Janela especificada incorretamente.')

    y = np.zeros(x.shape, dtype=x.dtype)

    start = N//2
    end   = -N//2+1 if N%2 else -N//2

    for index in range(nModes):
        
        # preenche as bordas do sinal com zeros
        x_padding = np.pad(x[:, index], (N//2, N//2), mode='constant')
        
        # calcula a média móvel 
        average = np.convolve(x_padding, h, mode='same')
        
        # obtém a saída de mesmo comprimento da entrada
        y[:, index] = average[start:end]
        
    return y