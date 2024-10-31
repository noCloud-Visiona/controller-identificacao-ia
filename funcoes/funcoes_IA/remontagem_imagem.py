from PIL import Image, TiffTags
import os
from osgeo import gdal
import numpy as np


Image.MAX_IMAGE_PIXELS = None  

def load_tile(tile_filename, tile_dir):
    tile_path = os.path.join(tile_dir, tile_filename)
    return Image.open(tile_path)

def get_tile_dimensions(tile):
    return tile.size 

def filtrar_metadados(metadados):
    # Filtra os metadados para manter apenas os suportados
    metadados_filtrados = {}
    tags_suportadas = TiffTags.TAGS_V2.values()  # Obtém as tags suportadas
    for tag, valor in metadados.items():
        if tag in tags_suportadas:
            # Verifica se o valor é do tipo inteiro e se está dentro do intervalo permitido
            if isinstance(valor, int):
                if 0 <= valor <= 4294967295:
                    metadados_filtrados[tag] = valor
                else:
                    print(f"Valor fora do intervalo para a tag {tag}: {valor}")
            elif isinstance(valor, (list, tuple)):
                # Verifica se todos os valores em uma lista estão dentro do intervalo
                if all(isinstance(v, int) and 0 <= v <= 4294967295 for v in valor):
                    metadados_filtrados[tag] = valor
                else:
                    print(f"Valores inválidos para a tag {tag}: {valor}")
            else:
                print(f"Tipo não suportado para a tag {tag}: {valor}")
    return metadados_filtrados

def remontar(tile_dir, tile_width, tile_height, tiles_per_col, tiles_per_row, filler_color, tiff_path, tile_name="RGB_merged_0", final_file_name="imagem_final_montada"):
    final_width = tile_width * tiles_per_row
    final_height = tile_height * tiles_per_col
    imagem_final = Image.new('RGB', (final_width, final_height))
    
    # Carregar a imagem TIFF original para extrair os metadados
    tiff_original = Image.open(tiff_path)  # Aqui não vai mais gerar o erro
    metadados = tiff_original.tag_v2
    print(f"Metadados originais: {metadados}")  # Imprime os metadados originais para depuração
    metadados_filtrados = filtrar_metadados(metadados)  
    print(f"Metadados filtrados: {metadados_filtrados}") 
    tiff_original = gdal.Open(tiff_path)
    metadados = tiff_original.GetMetadata()
    geotransform = tiff_original.GetGeoTransform()
    projection = tiff_original.GetProjection()
    # Itera sobre cada tile baseado nos índices da matriz
    for row_index in range(tiles_per_col):
        for col_index in range(tiles_per_row):
            # Nome do arquivo do tile, baseado na sua posição
            tile_filename = f"{row_index}_{col_index}_{tile_name}.png"
            print(tile_filename)
            try:
                tile = load_tile(tile_filename, tile_dir)
            except FileNotFoundError:
                print(f"Tile {tile_filename} não encontrado. Pulando.")
                continue
            # Verifica as dimensões do tile
            current_tile_width, current_tile_height = get_tile_dimensions(tile)
            x_position = col_index * tile_width
            y_position = row_index * tile_height
            # Criar um fundo do tamanho correto e colar o tile
            background = Image.new('RGB', (tile_width, tile_height), filler_color)
            background.paste(tile, (0, 0, current_tile_width, current_tile_height))
            imagem_final.paste(background, (x_position, y_position))
    imagem_array = np.array(imagem_final)

    driver = gdal.GetDriverByName("GTiff")
    output_tiff = driver.Create(final_file_name + ".tiff", final_width, final_height, 3, gdal.GDT_Byte, options=["COMPRESS=DEFLATE", "BIGTIFF=YES"])

    print("Output_tiff 0: ", output_tiff)

    # Configurações de metadados e geoinformação
    output_tiff.SetGeoTransform(geotransform)
    output_tiff.SetProjection(projection)
    output_tiff.SetMetadata(metadados)

    # Escrever cada banda na imagem
    print("Escrever cada banda na imagem")
    for i in range(3):  # Assumindo RGB, 3 bandas
        output_tiff.GetRasterBand(i + 1).WriteArray(imagem_array[:, :, i])

    print("Salvando Imagem:")
    output_tiff.FlushCache()
    print("Imagem final montada com sucesso, com metadados preservados!")