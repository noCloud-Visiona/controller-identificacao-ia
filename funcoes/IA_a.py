import funcoes.funcoes_IA.tratar_imagem as tratar_imagem
import funcoes.funcoes_IA.segmentar_imagem as segmentar_imagem
import funcoes.funcoes_IA.porcentagem_nuvem as porcentagem_nuvem
import funcoes.funcoes_IA.processar_resultado as processar_resultado
import os

def IA(image):
    # Tratar a imagem
    imagem_tratada = tratar_imagem.tratar_imagem(image)
    # Identificar a nuvem
    results = segmentar_imagem.segmentar_imagem(imagem_tratada)
    # Processar os resultados
    mask, merged_image = processar_resultado.processar_resultados(results, imagem_tratada)

    # Calcular a porcentagem da nuvem
    porcentagem = porcentagem_nuvem.porcentagem_nuvem(mask, image)
    
    # Retornar os três valores necessários
    return mask, merged_image, porcentagem
