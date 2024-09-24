from ultralytics import YOLO
from flask import jsonify
import shutil, os
from .serializador_de_imagem import transforma_imagem_em_json, transforma_json_em_imagem
from enums import Caminho

# campo que vai recebe o peso "best.pt" de treinamentos, caso queira testar o peso de um treinamento diferente, basta colocar o arquivo na pasta weights e apagar o atual
model = YOLO(Caminho.PESO.value)

def identificador_nuvem(image_path):

    # identifica nuvens e sombra de nuvens na imagem usando o peso no model, para então devolver a versão processada da imagem na pasta do predict_path
    model.predict(source=image_path, save=True)
    print('Predição realizada e imagem salva')
    
    supported_formats = {'bmp', 'jpg', 'png', 'tiff', 'mpo', 'webp', 'jpeg', 'dng', 'pfm', 'tif'}

    # verifica se há uma imagem com uma das extensões suportadas
    predict_path = None
    for file in os.listdir(Caminho.PASTA_PREDICT.value):
        if file.split('.')[-1].lower() in supported_formats:
            predict_path = os.path.join(Caminho.PASTA_PREDICT.value, file)
            break

    if predict_path:
        print(f"Imagem encontrada: {predict_path}")
    else:
        return jsonify({'error': 'Formato de imagem não suportado'}), 400

    # serializar a imagem em json e salvar no firebase
    if predict_path:
        image_json = transforma_imagem_em_json(predict_path)
        print("Imagem serializada em JSON: IA/img_desserializada/output_image.png")
        #print(image_json)

    # codigo que apaga a pasta predict para não ficar criando varios predicts como predict, predict2, predict3 e por ai em diante.
    shutil.rmtree(Caminho.PASTA_PREDICT.value)
    #Obs: Não usar comando "os" se não bloqueia por precisar ser cascata.

    ### salvar no banco a versão em json "image_json"

    output_image_path = "IA/img_desserializada/output_image.png"
    #Obs: sempre vai substituir a imagem anterior

    # desserializar Json de volta para imagem
    if (predict_path):
        transforma_json_em_imagem(image_json, Caminho.OUTPUT_IMAGE.value)
        print(f"Imagem desserializada e salva em: {Caminho.OUTPUT_IMAGE.value}")

    imagem_final = "IA/img_desserializada/output_image.png"

    # devolve a imagem serializada como Json, precisa mudar o return no app.py!
    #return image_json

    # devolve a imagem normal pós identificação da IA, precisa mudar o return no app.py!
    return Caminho.OUTPUT_IMAGE.value