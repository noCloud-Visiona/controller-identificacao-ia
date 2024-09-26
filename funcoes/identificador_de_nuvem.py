from ultralytics import YOLO
from flask import jsonify
import shutil, os, glob
from .serializador_de_imagem import transforma_imagem_em_json, transforma_json_em_imagem
from funcoes.enums import Caminho
import funcoes.funcoes_IA.tratar_imagem as tratar_imagem
import funcoes.funcoes_IA.segmentar_imagem as segmentar_imagem
import funcoes.funcoes_IA.porcentagem_nuvem as porcentagem_nuvem
import funcoes.funcoes_IA.processar_resultado as processar_resultado

# Carregar o modelo YOLO com o peso especificado
model = YOLO(Caminho.PESO.value)

def identificador_nuvem(image_path):
    print("Iniciando o identificador_nuvem...")

    model.predict(source=image_path, save=True)
    print('Predição realizada e imagem salva')

    # Encontra o diretório mais recente de predição
    latest_predict_dir = max(glob.glob('runs/segment/predict*'), key=os.path.getctime)
    print(f"Último diretório de predição: {latest_predict_dir}")

    supported_formats = {'bmp', 'jpg', 'png', 'tiff', 'mpo', 'webp', 'jpeg', 'dng', 'pfm', 'tif'}
    
    predict_path = None
    for file in os.listdir(latest_predict_dir):
        print(f"Arquivo encontrado: {file}")
        if file.split('.')[-1].lower() in supported_formats:
            predict_path = os.path.join(latest_predict_dir, file)
            break

    if predict_path:
        print(f"Imagem processada encontrada: {predict_path}")
    else:
        print("Erro: formato de imagem não suportado.")
        return jsonify({'error': 'Formato de imagem não suportado'}), 400

    imagem_tratada = tratar_imagem.tratar_imagem(predict_path)
    print("Imagem tratada com sucesso")

    results = segmentar_imagem.segmentar_imagem(imagem_tratada)
    print("Segmentação da imagem realizada")

    mask, merged_image = processar_resultado.processar_resultados(results, imagem_tratada)
    print("Resultado processado")

    porcentagem = porcentagem_nuvem.porcentagem_nuvem(mask, image_path)
    print(f"Porcentagem da imagem coberta pela máscara: {porcentagem:.2f}%")

    image_json = transforma_imagem_em_json(predict_path)
    print("Imagem serializada em JSON")

    transforma_json_em_imagem(image_json, Caminho.OUTPUT_IMAGE.value)
    print(f"Imagem desserializada e salva em: {Caminho.OUTPUT_IMAGE.value}")

    return Caminho.OUTPUT_IMAGE.value, porcentagem
