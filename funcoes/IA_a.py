from funcoes.funcoes_IA.segmentar_imagem import segmentar_imagens
from funcoes.funcoes_IA.recortar_imagem import recortar_imagem
from funcoes.funcoes_IA.remontagem_imagem import remontar
from funcoes.funcoes_IA.porcentagem_nuvem import porcentagem_nuvem
import funcoes.enums as Caminho
import os

def IA(image):

    recortar_imagem(tiff_path=image, image_output_dir=Caminho.Caminho.IMG_TILE.value, tile_size=640)

    segmentar_imagens()

    remontar(tile_dir=Caminho.Caminho.IMG_MERGED.value, tile_height=640, tile_width=640, tiles_per_col=10, tiles_per_row=10, filler_color=(0, 0, 0))
    remontar(tile_dir=Caminho.Caminho.IMG_MARK.value, tile_height=640, tile_width=640, tiles_per_col=10, tiles_per_row=10, filler_color=(0, 0, 0), tile_name="NIR_masked_output_0", final_file_name="mask_image_final")
    percent = porcentagem_nuvem(mask="./mask_image_final.png", image="./imagem_final_montada.png")
    
    return "./mask_image_final.png", "imagem_final_montada.png", percent
