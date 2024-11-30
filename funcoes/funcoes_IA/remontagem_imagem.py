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

    print("Processando o tile:", tile_filename)
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
    if final_file_name=="imagem_PNG_montada":
        thumbnail = imagem_final.resize((1000, 1000))   
        thumbnail.save(f'{final_file_name}_thumbnail_original.png')
        
    imagem_final.save(f'{final_file_name}.png')
    print("Imagem final ajustada montada com sucesso!")


def remontar(img_png, tiff_path, final_file_name="imagem_final_montada"):
    # Abrir o TIFF original para obter metadados
    tiff_original = gdal.Open(tiff_path)
    metadados = tiff_original.GetMetadata()
    geotransform = tiff_original.GetGeoTransform()
    projection = tiff_original.GetProjection()

    # Abrir o PNG com canal alfa
    imagem_png = Image.open(img_png).convert("RGBA")  # Preserva o canal alfa
    final_width, final_height = imagem_png.size  
    imagem_array = np.array(imagem_png)

    # Criar o TIFF de saída
    driver = gdal.GetDriverByName("GTiff")
    output_tiff = driver.Create(
        final_file_name + ".tiff",
        final_width,
        final_height,
        4,  
        gdal.GDT_Byte,
        options=["COMPRESS=DEFLATE", "BIGTIFF=YES"]
    )

    output_tiff.SetGeoTransform(geotransform)
    output_tiff.SetProjection(projection)
    output_tiff.SetMetadata(metadados)

    for i in range(3):  
        output_tiff.GetRasterBand(i + 1).WriteArray(imagem_array[:, :, i])

    alpha_band = output_tiff.GetRasterBand(4)
    alpha_band.WriteArray(imagem_array[:, :, 3]) 
    alpha_band.SetNoDataValue(0) 
    # Finalizar
    output_tiff.FlushCache()
    print("Imagem PNG convertida para TIFF com sucesso, com fundo transparente usando metadados do TIFF original!")

def verify_image_with_pillow(image_path):
    try:
        with Image.open(image_path) as img:
            img.verify()  # Verifica se a imagem está válida
        print(f"Imagem '{image_path}' verificada com sucesso.")
    except (IOError, SyntaxError) as e:
        print("Erro ao verificar a imagem com Pillow.")
        raise ValueError(f"Erro ao verificar a imagem '{image_path}': {e}")

def apply_inverse_mask_in_chunks(image_path, mask_path, output_path, chunk_size=1024):
    print("Procurando arquivos de imagem e máscara...")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Arquivo de imagem '{image_path}' não encontrado.")
    if not os.path.exists(mask_path):
        raise FileNotFoundError(f"Arquivo de máscara '{mask_path}' não encontrado.")
    
    print("Carregando imagem e máscara com PIL...")
    try:
        image = Image.open(image_path).convert("RGBA")
        mask = Image.open(mask_path).convert("L")
    except Exception as e:
        raise ValueError(f"Erro ao carregar a imagem ou máscara com PIL: {e}")
    
    image_width, image_height = image.size
    result_image = Image.new("RGBA", (image_width, image_height))

    for y in range(0, image_height, chunk_size):
        for x in range(0, image_width, chunk_size):
            print(f"Processando chunk na posição ({x}, {y})")
            box = (x, y, x + chunk_size, y + chunk_size)

            # Extrair o bloco da imagem e da máscara
            image_chunk = image.crop(box)
            mask_chunk = mask.crop(box)

            # Converter os blocos para arrays NumPy
            image_chunk_np = np.array(image_chunk)
            mask_chunk_np = np.array(mask_chunk)

            # Garantir que os tamanhos sejam compatíveis
            if image_chunk_np.shape[:2] != mask_chunk_np.shape:
                raise ValueError("A imagem e a máscara devem ter as mesmas dimensões por chunk.")

            # Inverter a máscara do chunk
            inverted_mask_chunk = cv2.bitwise_not(mask_chunk_np)

            # Aplicar a máscara inversa ao chunk da imagem
            result_chunk = cv2.bitwise_and(image_chunk_np[:, :, :3], image_chunk_np[:, :, :3], mask=inverted_mask_chunk)
            result_chunk = cv2.cvtColor(result_chunk, cv2.COLOR_RGB2BGRA)

            transparent_pixels = (inverted_mask_chunk == 0)
            result_chunk[transparent_pixels] = [0, 0, 0, 0]

            result_chunk_pil = Image.fromarray(result_chunk)
            result_image.paste(result_chunk_pil, box[:2])

    result_image_np = np.array(result_image)
    black_pixels = np.all(result_image_np[:, :, :3] == [0, 0, 0], axis=-1)
    result_image_np[black_pixels] = [0, 0, 0, 0]
    result_image = Image.fromarray(result_image_np)

    thumbnail = result_image.resize((1000, 1000))
    thumbnail_np = np.array(thumbnail)
    black_pixels_thumbnail = np.all(thumbnail_np[:, :, :3] == [0, 0, 0], axis=-1)
    thumbnail_np[black_pixels_thumbnail] = [0, 0, 0, 0]
    thumbnail = Image.fromarray(thumbnail_np)

    thumbnail.save(output_path + "_thumbnail.png")
    result_image.save(output_path + ".png")
    print(f"Imagem recortada com máscara inversa salva em {output_path}")


def apply_two_masks(image_path, mask1_path, mask2_path, output_path, color_mask1=(255, 0, 0, 128), color_mask2=(0, 0, 255, 128)):
    print("Procurando arquivos de imagem e máscaras...")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Arquivo de imagem '{image_path}' não encontrado.")
    if not os.path.exists(mask1_path):
        raise FileNotFoundError(f"Arquivo de máscara 1 '{mask1_path}' não encontrado.")
    if not os.path.exists(mask2_path):
        raise FileNotFoundError(f"Arquivo de máscara 2 '{mask2_path}' não encontrado.")
    
    print("Carregando imagem e máscaras com PIL...")
    try:
        image = Image.open(image_path).convert("RGBA")
        mask1 = Image.open(mask1_path).convert("L")  
        mask2 = Image.open(mask2_path).convert("L")
    except Exception as e:
        raise ValueError(f"Erro ao carregar a imagem ou máscaras com PIL: {e}")
    
    image_np = np.array(image)
    mask1_np = np.array(mask1)
    mask2_np = np.array(mask2)

    if image_np.shape[:2] != mask1_np.shape or image_np.shape[:2] != mask2_np.shape:
        raise ValueError("A imagem e as máscaras devem ter as mesmas dimensões.")

    print("Criando máscaras coloridas...")
    overlay_mask1 = np.zeros_like(image_np, dtype=np.uint8)
    overlay_mask2 = np.zeros_like(image_np, dtype=np.uint8)

    overlay_mask1[:, :, :3] = color_mask1[:3]
    overlay_mask1[:, :, 3] = color_mask1[3]
    
    overlay_mask2[:, :, :3] = color_mask2[:3]
    overlay_mask2[:, :, 3] = color_mask2[3]

    print("Aplicando máscaras sobre a imagem...")
    mask1_applied = mask1_np > 0
    mask2_applied = mask2_np > 0

    alpha1 = overlay_mask1[:, :, 3] / 255.0
    alpha2 = overlay_mask2[:, :, 3] / 255.0

    for c in range(3):  # Para R, G, B
        image_np[mask1_applied, c] = (
            image_np[mask1_applied, c] * (1 - alpha1[mask1_applied])
            + overlay_mask1[mask1_applied, c] * alpha1[mask1_applied]
        )
        image_np[mask2_applied, c] = (
            image_np[mask2_applied, c] * (1 - alpha2[mask2_applied])
            + overlay_mask2[mask2_applied, c] * alpha2[mask2_applied]
        )

    print("Removendo pixels completamente pretos...")
    black_pixels = np.all(image_np[:, :, :3] == 0, axis=-1)  # Localiza onde todos os canais RGB são 0
    image_np[black_pixels, 3] = 0  # Define o canal alfa como 0 (transparente) para esses pixels

    print("Redimensionando e salvando imagem final...")
    result_image = Image.fromarray(image_np)
    result_image = result_image.resize((1000, 1000))
    result_image.save(output_path + ".png", "PNG")
    print(f"Imagem com máscaras aplicadas e pixels pretos removidos salva em {output_path}.png")

def apply_mask_in_chunks(image_path, mask_path, output_path, chunk_size=1024, overlay_color=(255, 0, 0, 128)):
    print("Procurando arquivos de imagem e máscara...")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Arquivo de imagem '{image_path}' não encontrado.")
    if not os.path.exists(mask_path):
        raise FileNotFoundError(f"Arquivo de máscara '{mask_path}' não encontrado.")
    
    print("Carregando imagem e máscara com PIL...")
    try:
        image = Image.open(image_path).convert("RGBA")
        mask = Image.open(mask_path).convert("L")  # Carregar máscara em escala de cinza
    except Exception as e:
        raise ValueError(f"Erro ao carregar a imagem ou máscara com PIL: {e}")
    
    image_width, image_height = image.size

    print("Criando imagem de saída...")
    result_image = Image.new("RGBA", (image_width, image_height))

    for y in range(0, image_height, chunk_size):
        for x in range(0, image_width, chunk_size):
            print(f"Processando chunk na posição ({x}, {y})")
            box = (x, y, x + chunk_size, y + chunk_size)

            # Crop dos chunks de imagem e máscara
            image_chunk = image.crop(box)
            mask_chunk = mask.crop(box)
            
            # Converter chunks para numpy arrays
            image_chunk_np = np.array(image_chunk)
            mask_chunk_np = np.array(mask_chunk)

            if image_chunk_np.shape[:2] != mask_chunk_np.shape:
                raise ValueError("A imagem e a máscara devem ter as mesmas dimensões por chunk.")

            mask_applied = mask_chunk_np > 0  # Onde a máscara é diferente de zero (afetar)

            image_chunk_np[~mask_applied, 3] = 0  

            overlay_np = np.zeros_like(image_chunk_np, dtype=np.uint8)
            overlay_np[:, :, :3] = overlay_color[:3]  
            overlay_np[:, :, 3] = overlay_color[3]  
            
            alpha = overlay_np[:, :, 3] / 255.0  
            for c in range(3):  
                image_chunk_np[mask_applied, c] = (
                    image_chunk_np[mask_applied, c] * (1 - alpha[mask_applied])
                    + overlay_np[mask_applied, c] * alpha[mask_applied]
                )
            
            result_chunk_pil = Image.fromarray(image_chunk_np)
            result_image.paste(result_chunk_pil, box[:2])
    
    thumbnail = result_image.resize((1000, 1000))
    thumbnail.save(output_path + "_thumbnail.png")
    result_image.save(output_path + ".png")
    print(f"Imagem recortada salva em {output_path}")


   