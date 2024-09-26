from flask import Flask, request, jsonify
import funcoes.IA_a as IA_a
import os
import datetime
from funcoes.serializador_de_imagem import transforma_imagem_em_json
import cv2

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
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

    # Aqui estamos garantindo que a função IA retorna três valores
    mask_path, imagem_tratada, porcentagem_nuvem = IA_a.IA(image_path)

    nome_base = os.path.splitext(imagem.filename)[0]
    valor_increment = 1  # Ajuste conforme necessário

    id_unico = f"{nome_base}_{valor_increment}"

    data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
    hora_atual = datetime.datetime.now().strftime("%H:%M:%S")

    # Como `imagem_tratada` é um `numpy.ndarray`, você pode obter a resolução diretamente
    resolucao_imagem = f"{imagem_tratada.shape[1]}x{imagem_tratada.shape[0]}"  # largura x altura

    area_visivel_mapa = 100 - porcentagem_nuvem

    imagem_original_json = transforma_imagem_em_json(image_path)
    imagem_tratada_json = transforma_imagem_em_json('merged_output_with_color.png')  # Salvar como imagem antes de converter

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
