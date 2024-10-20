import rasterio
import numpy as np
import os
from PIL import Image
import cv2


def recortar_imagem(tiff_path, image_output_dir, tile_size):

    if not os.path.exists(image_output_dir):
       os.makedirs(image_output_dir)
    # Abrir o arquivo TIFF original (contendo apenas a banda NIR)
    with rasterio.open(tiff_path) as src:
        width, height = src.width, src.height
        transform = src.transform

        tile_count = 0

        for j in range(0, height, tile_size):  # Para as linhas (j)
            for i in range(0, width, tile_size):  # Para as colunas (i)
                window = rasterio.windows.Window(i, j, tile_size, tile_size)
                tile_transform = src.window_transform(window)
                tile = src.read(1, window=window)  # Ler apenas a banda 1, pois é a única presente
                
                linha_num = j // tile_size
                tile_filename_prefix = f"{linha_num}_{tile_count}"
                tile_count += 1

                image_filename = f"{tile_filename_prefix}_NIR.png"
                image_path = os.path.join(image_output_dir, image_filename)

                if tile.max() > 0:
                    nir_normalized = (tile / tile.max()) * 255
                else:
                    nir_normalized = np.zeros_like(tile)

                nir_image = nir_normalized.astype(np.uint8)
                img = Image.fromarray(nir_image, mode='L')  # 'L' para imagem em tons de cinza
                img.save(image_path)
                print(f"Imagem {image_filename}.")

            tile_count = 0

    print("Processo concluído!")
