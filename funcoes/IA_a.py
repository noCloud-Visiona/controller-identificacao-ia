from funcoes_IA.segmentar_imagem import segmentar_imagens
from funcoes_IA.recortar_imagem import recortar_imagem
from funcoes_IA.remontagem_imagem import remontar
import enums as Caminho
import os

def IA(image):

    #recortar_imagem(tiff_path=image, image_output_dir=Caminho.Caminho.IMG_TILE.value, tile_size=640)

    #segmentar_imagens()

    remontar(tile_dir=Caminho.Caminho.IMG_MERGED.value, tile_height=640, tile_width=640, tiles_per_col=23, tiles_per_row=23, filler_color=(0, 0, 0))
