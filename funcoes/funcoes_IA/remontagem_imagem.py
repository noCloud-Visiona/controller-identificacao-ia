from PIL import Image
import os

# Função para carregar um tile com base no nome do arquivo
def load_tile(tile_filename, tile_dir):
    tile_path = os.path.join(tile_dir, tile_filename)
    return Image.open(tile_path)

def get_tile_dimensions(tile):
    return tile.size 


def remontar(tile_dir, tile_width, tile_height, tiles_per_col, tiles_per_row, filler_color):
    final_width = tile_width * tiles_per_row
    final_height = tile_height * tiles_per_col
    imagem_final = Image.new('RGB', (final_width, final_height))
    # Itera sobre cada tile baseado nos índices da matriz
    for row_index in range(tiles_per_col):
        for col_index in range(0, tiles_per_row):
            # Nome do arquivo do tile, baseado na sua posição (você pode ajustar conforme necessário)
            tile_filename = f"{row_index}_{col_index}_NIR_merged_0.png"
            print(tile_filename)

            try:
                tile = load_tile(tile_filename, tile_dir)
            except FileNotFoundError:
                print(f"Tile {tile_filename} não encontrado. Pulando.")
                continue
            print(tile_filename)
            # Verifica as dimensões do tile
            current_tile_width, current_tile_height = get_tile_dimensions(tile)

            x_position = col_index * tile_width
            y_position = row_index * tile_height

            background = Image.new('RGB', (tile_width, tile_height), filler_color)

            background.paste(tile, (0, 0, current_tile_width, current_tile_height))

            imagem_final.paste(background, (x_position, y_position))

    # Salva a imagem final montada
    imagem_final.save('imagem_final_montada_ajustada.png')
    print("Imagem final ajustada montada com sucesso!")

#remontar(tile_dir, tile_width, tile_height, tiles_per_col, filler_color)
