from enum import Enum

class Caminho(Enum):
    PESO = './IA/weights/best_jonatas.pt'
    PASTA_PREDICT = 'runs/segment/predict/'
    OUTPUT_IMAGE = 'IA/img_desserializada/output_image.png'
    IMG_TILE = './IA/img_tile/'
    IMG_TIFF = './IA/img/'
    IMG_OUTPUT = './IA/img_desserializada/'
    IMG_MERGED = './IA/img_merged/'