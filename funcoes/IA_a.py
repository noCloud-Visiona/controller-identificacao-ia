from funcoes.funcoes_IA.segmentar_imagem import segmentar_imagens
from funcoes.funcoes_IA.recortar_imagem import recortar_imagem_rgb
from funcoes.funcoes_IA.remontagem_imagem import remontar, remontar_rgb, apply_mask_in_chunks, apply_inverse_mask_in_chunks
from funcoes.funcoes_IA.porcentagem_nuvem import porcentagem_nuvem
import funcoes.enums as Caminho
import os

def IA(image):

    #tiles = recortar_imagem_rgb(tiff_path=image, image_output_dir=Caminho.Caminho.IMG_TILE.value, tile_size=1024)

    #segmentar_imagens()

    #remontar_rgb(tile_dir=Caminho.Caminho.IMG_TILE.value, tile_height=1024, tile_width=1024, tiles_per_col=tiles[0]+1, tiles_per_row=tiles[1]+1, filler_color=(0, 0, 0), tile_name="RGB", final_file_name="imagem_PNG_montada")
    #remontar_rgb(tile_dir=Caminho.Caminho.IMG_MARK.value, tile_height=1024, tile_width=1024, tiles_per_col=tiles[0]+1, tiles_per_row=tiles[1]+1, filler_color=(0, 0, 0), tile_name="RGB_masked_output_0", final_file_name="mask_image_PNG")

    #apply_mask_in_chunks(image_path="./imagem_PNG_montada.png", mask_path="./mask_image_PNG.png", output_path="./imagem_final_cortada_nuvem_montada.png")
    #apply_inverse_mask_in_chunks(image_path="./imagem_PNG_montada.png", mask_path="./mask_image_PNG.png", output_path="./imagem_final_cortada_sem_nuvem.png")



    #remontar(img_png="./imagem_final_cortada_nuvem_montada.png", tiff_path=image, final_file_name="imagem_final_cortada_nuvem_montada")
    remontar(img_png="./imagem_final_cortada_sem_nuvem.png", tiff_path=image, final_file_name="imagem_final_cortada_sem_nuvem")
    


    #percent = porcentagem_nuvem(mask="./mask_image_final.png", img="./imagem_final_montada.png")
    print("Retornando Imagem")
    #return "./mask_image_final.tiff", "./imagem_final_montada.tiff" , 0
