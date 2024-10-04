from PIL import Image
import os


# Diretório onde os tiles estão armazenados
tile_dir = 'img/tiff_imagem'

# Dimensões padrão dos tiles (máximo)
tile_width, tile_height = 640, 640

# Número de tiles por linha e coluna
tiles_per_row = 23  # Número de tiles na horizontal
tiles_per_col = 23  # Número de tiles na vertical

filler_color = (0, 0, 0)  # Cor preta para preencher as áreas vazias

# Função para carregar um tile com base no nome do arquivo
def load_tile(tile_filename, tile_dir):
    tile_path = os.path.join(tile_dir, tile_filename)
    return Image.open(tile_path)

# Função que retorna as dimensões de um tile
def get_tile_dimensions(tile):
    return tile.size  # Retorna (largura, altura) do tile


def remontar(tile_dir, tile_width, tile_height, tiles_per_col, filler_color):
    final_width = tile_width * tiles_per_row
    final_height = tile_height * tiles_per_col
    imagem_final = Image.new('RGB', (final_width, final_height))
    # Itera sobre cada tile baseado nos índices da matriz
    for row_index in range(tiles_per_col):
        for col_index in range(tiles_per_row, tiles_per_row):
            # Nome do arquivo do tile, baseado na sua posição (você pode ajustar conforme necessário)
            tile_filename = f"{row_index}_{col_index}_NIR.png"

            # Carrega o tile
            try:
                tile = load_tile(tile_filename, tile_dir)
            except FileNotFoundError:
                print(f"Tile {tile_filename} não encontrado. Pulando.")
                continue

            # Verifica as dimensões do tile
            current_tile_width, current_tile_height = get_tile_dimensions(tile)

            # Calcula a posição na imagem final
            x_position = col_index * tile_width
            y_position = row_index * tile_height

            # Cria um fundo do tamanho correto para o tile com a cor de preenchimento
            background = Image.new('RGB', (tile_width, tile_height), filler_color)

            # Cola o tile na imagem de fundo (caso o tile seja menor, ele é centralizado)
            background.paste(tile, (0, 0, current_tile_width, current_tile_height))

            # Coloca o tile (com o fundo) na imagem final na posição correta
            imagem_final.paste(background, (x_position, y_position))

    # Salva a imagem final montada
    imagem_final.save('imagem_final_montada_ajustada.png')
    print("Imagem final ajustada montada com sucesso!")

#remontar(tile_dir, tile_width, tile_height, tiles_per_col, filler_color)
