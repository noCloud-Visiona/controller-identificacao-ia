from funcoes.funcoes_IA.segmentar_imagem import segmentar_imagens
from funcoes.funcoes_IA.recortar_imagem import recortar_imagem_rgb
from funcoes.funcoes_IA.remontagem_imagem import remontar, remontar_rgb, apply_mask
from funcoes.funcoes_IA.porcentagem_nuvem import porcentagem_nuvem
import funcoes.enums as Caminho
import os

def IA(image):

    #recortar_imagem_rgb(tiff_path=image, image_output_dir=Caminho.Caminho.IMG_TILE.value, tile_size=640)

    #segmentar_imagens()

    #remontar_rgb(tile_dir=Caminho.Caminho.IMG_TILE.value, tile_height=640, tile_width=640, tiles_per_col=90, tiles_per_row=88, filler_color=(0, 0, 0), tile_name="RGB", final_file_name="imagem_PNG_montada")
    #remontar_rgb(tile_dir=Caminho.Caminho.IMG_MARK.value, tile_height=640, tile_width=640, tiles_per_col=90, tiles_per_row=88, filler_color=(0, 0, 0), tile_name="RGB_masked_output_0", final_file_name="mask_image_PNG")

    apply_mask(image_path="./imagem_PNG_montada.png", mask_path="./mask_image_PNG.png", output_path="./imagem_final_cortada_nuvem_montada.png")

    #remontar(tile_dir=Caminho.Caminho.IMG_MERGED.value, tile_height=640, tile_width=640, tiles_per_col=90, tiles_per_row=88, filler_color=(0, 0, 0), tiff_path=image)
    #remontar(tile_dir=Caminho.Caminho.IMG_MARK.value, tile_height=640, tile_width=640, tiles_per_col=90, tiles_per_row=88, filler_color=(0, 0, 0), tile_name="RGB_masked_output_0", final_file_name="mask_image_final", tiff_path=image)
    


    #percent = porcentagem_nuvem(mask="./mask_image_final.png", img="./imagem_final_montada.png")
    
    #return "./mask_image_final.png", "imagem_final_montada.png", percent
