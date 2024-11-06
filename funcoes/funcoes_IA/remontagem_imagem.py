from PIL import Image, TiffTags
import os
from osgeo import gdal
import numpy as np
import cv2
import concurrent.futures



Image.MAX_IMAGE_PIXELS = None  

def load_tile(tile_filename, tile_dir):
    return Image.open(os.path.join(tile_dir, tile_filename))

def get_tile_dimensions(tile):
    return tile.size 

def create_background_tile(tile_width, tile_height, filler_color):
    return Image.new('RGB', (tile_width, tile_height), filler_color)

def process_tile(row_index, col_index, tile_width, tile_height, tile_name, tile_dir, filler_color):
    tile_filename = f"{row_index}_{col_index}_{tile_name}.png"
    tile_path = os.path.join(tile_dir, tile_filename)

    if not os.path.exists(tile_path):
        placeholder_tile = Image.new('RGB', (tile_width, tile_height), filler_color)
        return placeholder_tile, (col_index * tile_width, row_index * tile_height)


    tile = load_tile(tile_filename, tile_dir)
    current_tile_width, current_tile_height = get_tile_dimensions(tile)

    background_tile = create_background_tile(tile_width, tile_height, filler_color)
    background_tile.paste(tile, (0, 0, current_tile_width, current_tile_height))

    return background_tile, (col_index * tile_width, row_index * tile_height)

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


def remontar_rgb(tile_dir, tile_width, tile_height, tiles_per_col, tiles_per_row, filler_color, tile_name="RGB_merged_0", final_file_name="imagem_final_montada"):
    final_width = tile_width * tiles_per_row
    final_height = tile_height * tiles_per_col
    imagem_final = Image.new('RGB', (final_width, final_height))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_tile = {
            executor.submit(process_tile, row, col, tile_width, tile_height, tile_name, tile_dir, filler_color): (row, col)
            for row in range(tiles_per_col)
            for col in range(tiles_per_row)
        }

        for future in concurrent.futures.as_completed(future_to_tile):
            tile, position = future.result()
            if tile:
                imagem_final.paste(tile, position)

    imagem_final.save(f'{final_file_name}.png')
    print("Imagem final ajustada montada com sucesso!")


def remontar(tile_dir, tile_width, tile_height, tiles_per_col, tiles_per_row, filler_color, tiff_path, tile_name="RGB_merged_0", final_file_name="imagem_final_montada"):
    final_width = tile_width * tiles_per_row
    final_height = tile_height * tiles_per_col
    imagem_final = Image.new('RGB', (final_width, final_height))
    
    tiff_original = Image.open(tiff_path)  
    metadados = tiff_original.tag_v2
    print(f"Metadados originais: {metadados}")  # Imprime os metadados originais para depuração
    metadados_filtrados = filtrar_metadados(metadados)  
    print(f"Metadados filtrados: {metadados_filtrados}") 
    tiff_original = gdal.Open(tiff_path)
    metadados = tiff_original.GetMetadata()
    geotransform = tiff_original.GetGeoTransform()
    projection = tiff_original.GetProjection()
    for row_index in range(tiles_per_col):
        for col_index in range(tiles_per_row):
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

def verify_image_with_pillow(image_path):
    try:
        with Image.open(image_path) as img:
            img.verify()  # Verifica se a imagem está válida
        print(f"Imagem '{image_path}' verificada com sucesso.")
    except (IOError, SyntaxError) as e:
        print("Erro ao verificar a imagem com Pillow.")
        raise ValueError(f"Erro ao verificar a imagem '{image_path}': {e}")

def apply_inverse_mask(image_path, mask_path, output_path):
    print("Procurando arquivos de imagem e máscara...")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Arquivo de imagem '{image_path}' não encontrado.")
    if not os.path.exists(mask_path):
        raise FileNotFoundError(f"Arquivo de máscara '{mask_path}' não encontrado.")
    
    # Carrega a imagem com PIL e converte para o formato OpenCV
    print("Carregando imagem com PIL e convertendo para OpenCV...")
    try:
        image = Image.open(image_path)
        image = np.array(image)
    except Exception as e:
        raise ValueError(f"Erro ao carregar a imagem '{image_path}' com PIL: {e}")
    
    # Carrega a máscara com PIL, converte para escala de cinza e inverte a máscara
    print("Carregando máscara com PIL, convertendo e invertendo...")
    try:
        mask = Image.open(mask_path).convert("L")  # "L" para escala de cinza
        mask = np.array(mask)
        mask = cv2.bitwise_not(mask)  # Inverte a máscara
    except Exception as e:
        raise ValueError(f"Erro ao carregar a máscara '{mask_path}' com PIL: {e}")

    # Verifica se a imagem e a máscara têm as mesmas dimensões
    print("Verificando o tamanho da máscara...")
    if image.shape[:2] != mask.shape:
        raise ValueError("A imagem e a máscara devem ter as mesmas dimensões.")

    # Aplica a máscara inversa à imagem, removendo as áreas em branco
    print("Aplicando máscara inversa à imagem...")
    result = cv2.bitwise_and(image, image, mask=mask)

    # Salva o resultado
    cv2.imwrite(output_path, result)
    print(f"Imagem recortada com máscara inversa salva em {output_path}")


def apply_mask(image_path, mask_path, output_path):
    print("Procurando arquivos de imagem e máscara...")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Arquivo de imagem '{image_path}' não encontrado.")
    if not os.path.exists(mask_path):
        raise FileNotFoundError(f"Arquivo de máscara '{mask_path}' não encontrado.")
    
    print("Carregando imagem com PIL e convertendo para OpenCV...")
    try:
        image = Image.open(image_path)
        image = np.array(image)
    except Exception as e:
        raise ValueError(f"Erro ao carregar a imagem '{image_path}' com PIL: {e}")
    
    print("Carregando máscara com PIL e convertendo para OpenCV...")
    try:
        mask = Image.open(mask_path).convert("L")  # "L" para escala de cinza
        mask = np.array(mask)
    except Exception as e:
        raise ValueError(f"Erro ao carregar a máscara '{mask_path}' com PIL: {e}")

    print("Verificando o tamanho da máscara...")
    if image.shape[:2] != mask.shape:
        raise ValueError("A imagem e a máscara devem ter as mesmas dimensões.")

    print("Aplicando máscara à imagem...")
    result = cv2.bitwise_and(image, image, mask=mask)

    cv2.imwrite(output_path, result)
    print(f"Imagem recortada salva em {output_path}")