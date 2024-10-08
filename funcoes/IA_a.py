from funcoes_IA.segmentar_imagem import segmentar_imagens
from funcoes_IA.recortar_imagem import recortar_imagem
import funcoes.enums as Caminho
import os

def IA(image):

    recortar_imagem(tiff_path=image, image_output_dir=Caminho.Caminho.IMG_TILE.value, tile_size=640)

    output_mask_path, merged_image, porcentagem = segmentar_imagens()

    # Retornar os três valores necessários
    return output_mask_path, merged_image, porcentagem
