from flask import Flask, request, jsonify
import funcoes.IA_a as IA_a
import os
import datetime
from funcoes.serializador_de_imagem import transforma_imagem_em_json
import cv2
from firebase import db

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    #espera um json ou texto com o atributo id que será o id do usuario
    id_usuario = None

    if request.is_json:
        data = request.get_json()
        id_usuario = data.get('id')
    else:
        if 'id' in request.form:
            id_usuario = request.form['id']

    #espera uma imagem a ser tratada pela IA
    if not request.files:
        return jsonify({'error': 'Nenhuma imagem provida'}), 400

    imagem = next(iter(request.files.values()))

    image_dir = "IA/img/"
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    image_path = os.path.join(image_dir, imagem.filename)
    imagem.save(image_path)

    supported_formats = {'bmp', 'jpg', 'png', 'tiff', 'mpo', 'webp', 'jpeg', 'dng', 'pfm', 'tif'}

    if image_path.split('.')[-1].lower() not in supported_formats:
        os.remove(image_path)
        return jsonify({'error': 'Formato de imagem não suportado'}), 400

    print(f"Imagem encontrada: {image_path}")

    imagem_original_json = transforma_imagem_em_json(image_path)

    # Aqui estamos garantindo que a função IA retorna três valores
    mask_path, imagem_tratada, porcentagem_nuvem = IA_a.IA(image_path)

    # Apaga a imagem da pasta local após ter a versão em json
    supported_formats = {'bmp', 'jpg', 'png', 'tiff', 'mpo', 'webp', 'jpeg', 'dng', 'pfm', 'tif'}
    for file in os.listdir(image_dir):
        if file.split('.')[-1].lower() in supported_formats:
            file_path = os.path.join(image_dir, file)
            os.remove(file_path)

    nome_base = os.path.splitext(imagem.filename)[0]


    ### Montagem do json de resposta daqui pra baixo


    data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
    hora_atual = datetime.datetime.now().strftime("%H:%M:%S")

    # Como `imagem_tratada` é um `numpy.ndarray`, você pode obter a resolução diretamente
    resolucao_imagem = f"{imagem_tratada.shape[1]}x{imagem_tratada.shape[0]}"  # largura x altura

    area_visivel_mapa = 100 - porcentagem_nuvem
    porcentagem_nuvem = round(porcentagem_nuvem, 2)
    area_visivel_mapa = round(area_visivel_mapa, 2)

    imagem_tratada_json = transforma_imagem_em_json('merged_output_with_color.png')  # Salvar como imagem antes de converter

    # Salvando no firestorm a imagem json
    collection_ref = db.collection("historico_imagens_ia")
    collection_ref.add({"id": id_usuario, "imagem_json": imagem_tratada_json, "data": data_atual, "hora": hora_atual})

    # Count de quantas imagens salvas tem, para acrescentar +1
    docs = collection_ref.stream()
    doc_count = sum(1 for _ in docs)
    
    id_unico = f"{nome_base}_{doc_count}"

    resposta = {
        "id": id_unico,
        "data": data_atual,
        "hora": hora_atual,
        "geometry": {
            "type": "Polygon",
            "coordinates": None
        },
        "resolucao_imagem": resolucao_imagem,
        "satelite": "CBERS4A",
        "sensor": "WPM",
        "percentual_nuvem": porcentagem_nuvem,
        "area_visivel_mapa": area_visivel_mapa,
        "imagem": None,
        "thumbnail": imagem_original_json,
        "img_tratada": imagem_tratada_json
    }

    return jsonify(resposta)



if __name__ == '__main__':
    app.run(debug=True)
