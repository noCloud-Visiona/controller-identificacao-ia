from funcoes.funcoes_IA.segmentar_imagem import segmentar_imagens
from funcoes.funcoes_IA.recortar_imagem import recortar_imagem_rgb, limpar_diretorios
from funcoes.funcoes_IA.remontagem_imagem import remontar, remontar_rgb, apply_mask_in_chunks, apply_inverse_mask_in_chunks
from funcoes.funcoes_IA.porcentagem_nuvem import porcentagem_nuvem
import funcoes.enums as Caminho
import os

def IA(image):

    tiles = recortar_imagem_rgb(tiff_path=image, image_output_dir=Caminho.Caminho.IMG_TILE.value, tile_size=1024)

    segmentar_imagens()

    remontar_rgb(tile_dir=Caminho.Caminho.IMG_TILE.value, tile_height=1024, tile_width=1024, tiles_per_col=tiles[0]+1, tiles_per_row=tiles[1]+1, filler_color=(0, 0, 0), tile_name="RGB", final_file_name="imagem_PNG_montada")
    remontar_rgb(tile_dir=Caminho.Caminho.IMG_MARK.value, tile_height=1024, tile_width=1024, tiles_per_col=tiles[0]+1, tiles_per_row=tiles[1]+1, filler_color=(0, 0, 0), tile_name="RGB_shadow_mask", final_file_name="mask_shadow_PNG")
    remontar_rgb(tile_dir=Caminho.Caminho.IMG_MARK.value, tile_height=1024, tile_width=1024, tiles_per_col=tiles[0]+1, tiles_per_row=tiles[1]+1, filler_color=(0, 0, 0), tile_name="RGB_cloud_mask", final_file_name="mask_cloud_PNG")

    apply_mask_in_chunks(image_path="./imagem_PNG_montada.png", mask_path="./mask_cloud_PNG.png", output_path="./nuvem")
    apply_mask_in_chunks(image_path="./imagem_PNG_montada.png", mask_path="./mask_shadow_PNG.png", output_path="./sombra")
    apply_inverse_mask_in_chunks(image_path="./imagem_PNG_montada.png", mask_path="./mask_cloud_PNG.png", output_path="./sem_nuvem")
    apply_inverse_mask_in_chunks(image_path="./imagem_PNG_montada.png", mask_path="./mask_shadow_PNG.png", output_path="./sem_sombra")

    remontar(img_png="./nuvem.png", tiff_path=image, final_file_name="imagem_nuvem_montada")
    remontar(img_png="./sombra.png", tiff_path=image, final_file_name="imagem_sombra_montada")
    remontar(img_png="./sem_nuvem.png", tiff_path=image, final_file_name="imagem_sem_nuvem_montada")
    remontar(img_png="./sem_sombra.png", tiff_path=image, final_file_name="imagem_sem_sombra_montada")    

    #percent = porcentagem_nuvem(mask="./mask_image_PNG.png", img="./imagem_PNG_montada.png")
    #print(f"A porcentagem de nuvem na imagem é de {percent}%")

    #limpar_diretorios(Caminho.Caminho.IMG_TILE.value, Caminho.Caminho.IMG_MARK.value, Caminho.Caminho.IMG_MERGED.value, Caminho.Caminho.IMG_TIFF.value, "./mask_image_PNG.png", "./imagem_PNG_montada.png", "./imagem_final_cortada_nuvem_montada.png", "./imagem_final_cortada_sem_nuvem.png")

    return "./imagem_final_cortada_nuvem_montada.tiff", "./imagem_final_cortada_sem_nuvem.tiff" , 0
