import numpy as np

def interpolator(x, mu):
    """
    Interpolador cúbico baseado na estrutura de Farrow

    Parameters
    ----------
    x : np.array
        matriz de 4 elementos para interpolação cúbica.
    
    mu : float
        parâmetro de interpolação.

    Returns
    -------
    y : float
        sinal interpolado.
    
    Referências
    -----------
        [1] Digital Coherent Optical Systems, Architecture and Algorithms
        
        [2] C. Farrow, A continuously variable digital delay element, in IEEE International Symposium on Circuits and Systems, vol. 3 (1988), pp. 2641–2645
    """
    
    return (
        x[0] * (-1/6 * mu**3 + 0 * mu**2 + 1/6 * mu + 0) +
        x[1] * (1/2 * mu**3 + 1/2 * mu**2 - mu + 0) +
        x[2] * (-1/2 * mu**3 - mu**2 + 1/2 * mu + 1) +
        x[3] * (1/6 * mu**3 + 1/2 * mu**2 + 1/3 * mu + 0)
    )

def gardnerTED(x, isNyquist):
    """
    Gardner TED algorithm in time domain.

    Parameters
    ----------
    x : np.array
        Matriz de três amostras para o calculo do erro.

    isNyquist : bool
        sinaliza um pulso da família de nyquist.

    Returns
    -------
    error: float
        magnitude do erro.
    
    Referências
    -----------
        [1] Digital Coherent Optical Systems, Architecture and Algorithms

        [2] F. Gardner, A BPSK/QPSK timing-error detector for sampled receivers. IEEE Trans. Commun. 34(5), 423–429 (1986)
    """
    if isNyquist:
        error = np.abs(x[1]) ** 2 * (np.abs(x[0]) ** 2 - np.abs(x[2]) ** 2)
    else:
        error = np.real(np.conj(x[1]) * (x[2] - x[0]))
    return error

def clockRecovery(x, paramCLK):
    """
    Executa a recuperação de clock no sinal 'x' usando uma estrutura DPLL 
    consistindo em um interpolador, um TED, um filtro de loop e um NCO. 

    Parameters
    ----------
    x : np.array
        sinal de entrada com duas orientações de polarização obtido em 2 Sa/Símbolo.
    
    paramCLK : struct

        - paramCLK.ki (float): Constante da parte integral do filtro de loop. (ganho integrativo)

        - paramCLK.kp (float): Constante da parte proporcional do filtro de loop. (ganho proporcional)

        - paramCLK.Nyquist (bool): Sinaliza um pulso de Nyquist.

        - paramCLK.nSymbols (int): Número de símbolos transmitidos.

        - param.ppm (int): Desvio esperado da taxa máxima de clock. [ppm]

    Returns
    -------
    tuple
        - y (np.array): Sinal obtido após a recuperação do clock.
        - ted_values (np.array): O sinal oscilante produzido pelo NCO.

    Referências
    -----------
        [1] Digital Coherent Optical Systems, Architecture and Algorithms
        
        [2] C. Farrow, A continuously variable digital delay element, in IEEE International Symposium on Circuits and Systems, vol. 3 (1988), pp. 2641–2645

        [3] F. Gardner, A BPSK/QPSK timing-error detector for sampled receivers. IEEE Trans. Commun. 34(5), 423–429 (1986)
    """

    length, nModes = x.shape
    nSymbols = paramCLK.nSymbols

    y = np.zeros((int((1 - paramCLK.ppm / 1e6) * length), nModes), dtype="complex")
    
    # obtenha o sinal produzido pelo NCO
    nco_values = np.zeros(x.shape, dtype="float")

    y[:2] = x[:2]
    
    for indMode in range(nModes):
        
        # parâmetros do dpll:
        out_nco = 0.5           
        out_LF  = 1             
        
        n = 2
        fractional_interval = 0     # mun                  
        basePoint = n               # mn                     
        
        integrative = out_LF 

        while n < length - 1 and basePoint <= length:
            y[n, indMode] = interpolator(x[basePoint - 2: basePoint + 2, indMode], fractional_interval)

            if n % 2 == 0:
                # obtenha o erro de tempo 
                errorTED = gardnerTED(y[n - 2: n + 1, indMode], paramCLK.Nyquist)
                
                # loop PI filter
                integrative += paramCLK.ki * errorTED
                proportional = paramCLK.kp * errorTED
                out_LF = proportional + integrative

            eta_nco = out_nco - out_LF

            if eta_nco > -1 and eta_nco < 0:
                basePoint += 1 # Neste caso, a próxima amostra mn+1 é usada como ponto base para a próxima atualização do interpolador
            elif eta_nco >= 0:
                basePoint += 2 # Neste caso, uma amostra é ignorada e a outra amostra é usada como ponto base para a próxima atualização do interpolador.

            out_nco = (out_nco - out_LF) % 1
            fractional_interval = out_nco / out_LF

            nco_values[n, indMode] = eta_nco
            
            # atualiza o indexador temporal 'n'   
            n += 1
        
    if nSymbols * 2 < len(y):
        return y[0:nSymbols * 2, :], nco_values
    else:    
        return y, nco_values