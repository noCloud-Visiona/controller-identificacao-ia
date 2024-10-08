import funcoes.funcoes_IA.tratar_imagem as tratar_imagem
from funcoes.funcoes_IA.segmentar_imagem import segmentar_imagens
import funcoes.funcoes_IA.porcentagem_nuvem as porcentagem_nuvem
import funcoes.funcoes_IA.processar_resultado as processar_resultado
import funcoes.funcoes_IA.recortar_imagem as recortar_imagem
import funcoes.enums as Caminho
import os

def IA(image):
    # Tratar a imagem
    imagem_tratada = tratar_imagem.tratar_imagem(image)

    recortar_imagem.recortar_imagem(tiff_path=image, image_output_dir=Caminho.Caminho.IMG_TILE.value, tile_size=640)

    results = segmentar_imagens()


    

    mask, merged_image = processar_resultado.processar_resultados(results, imagem_tratada)

    # Calcular a porcentagem da nuvem
    porcentagem = porcentagem_nuvem.porcentagem_nuvem(mask, image)
    
    # Retornar os três valores necessários
    return mask, merged_image, porcentagem
