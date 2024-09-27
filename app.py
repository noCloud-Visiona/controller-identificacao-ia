from flask import Flask, make_response, request, jsonify, send_file
import funcoes.IA_a as IA_a
import os
import datetime
from funcoes.serializador_de_imagem import transforma_imagem_em_json
import cv2
import json
from io import BytesIO

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

@app.route('/predict_with_image', methods=['POST'])
def predict_with_image():
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

    mask_path, imagem_tratada, porcentagem_nuvem = IA_a.IA(image_path)

    nome_base = os.path.splitext(imagem.filename)[0]
    valor_increment = 1  # Ajuste conforme necessário

    id_unico = f"{nome_base}_{valor_increment}"

    data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
    hora_atual = datetime.datetime.now().strftime("%H:%M:%S")

    resolucao_imagem = f"{imagem_tratada.shape[1]}x{imagem_tratada.shape[0]}"  # largura x altura
    area_visivel_mapa = 100 - porcentagem_nuvem

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
    }

    # Criar a resposta multipart
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    parts = []

    # Adicionar o JSON como uma parte
    parts.append(f'--{boundary}')
    parts.append('Content-Disposition: form-data; name="json"')
    parts.append('Content-Type: application/json; charset=utf-8')
    parts.append('')
    parts.append(json.dumps(resposta))  # Agora o json estará definido corretamente

    # Adicionar a imagem tratada como uma parte
    img_tratada_io = BytesIO()
    _, img_tratada_encoded = cv2.imencode('.png', imagem_tratada)
    img_tratada_io.write(img_tratada_encoded.tobytes())
    img_tratada_io.seek(0)
    
    parts.append(f'--{boundary}')
    parts.append('Content-Disposition: form-data; name="img_tratada"; filename="imagem_tratada.png"')
    parts.append('Content-Type: image/png')
    parts.append('')
    parts.append(img_tratada_io.read().decode('latin1'))  # Use 'latin1' para converter bytes para string

    # Adicionar a thumbnail como uma parte
    img_thumbnail = cv2.resize(imagem_tratada, (100, 100))
    thumbnail_io = BytesIO()
    _, thumbnail_encoded = cv2.imencode('.png', img_thumbnail)
    thumbnail_io.write(thumbnail_encoded.tobytes())
    thumbnail_io.seek(0)
    
    parts.append(f'--{boundary}')
    parts.append('Content-Disposition: form-data; name="thumbnail"; filename="thumbnail.png"')
    parts.append('Content-Type: image/png')
    parts.append('')
    parts.append(thumbnail_io.read().decode('latin1'))

    # Finalizar a resposta multipart
    parts.append(f'--{boundary}--')
    parts.append('')

    body = '\r\n'.join(parts)

    response = make_response(body)
    response.headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
    return response

if __name__ == '__main__':
    app.run(debug=True)
