from flask import Flask, make_response, request, jsonify, send_file
import funcoes.IA_a as IA_a
import os
import datetime
from funcoes.serializador_de_imagem import transforma_imagem_em_json, transforma_json_em_imagem
import cv2
import json
from io import BytesIO
import base64
import numpy as np

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
    
    # Salvando a imagem tratada em um arquivo
    tratada_path = "IA/img/merged_output_with_color.png"
    cv2.imwrite(tratada_path, imagem_tratada)
    
    # Convertendo a imagem tratada para JSON Base64
    with open(tratada_path, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode('utf-8')

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
        "img_tratada": encoded_string  # Agora a imagem está em Base64 correta
    }

    return jsonify(resposta)

@app.route('/show_image', methods=['POST'])
def show_image():
    # Recebe o JSON com a imagem codificada
    json_data = request.get_json()

    # Chama a função para transformar a imagem codificada em um arquivo PNG
    success, mensagem = transforma_json_em_imagem(json_data, "IA/img/output_image.png")

    if success:
        # Retorna a imagem decodificada
        try:
            return send_file("IA/img/output_image.png", mimetype='image/png'), 200
        except FileNotFoundError:
            return jsonify({"message": "Erro: Imagem não encontrada"}), 404
    else:
        # Em caso de erro, retorna a mensagem de erro
        return jsonify({"message": mensagem}), 400

def transforma_json_em_imagem(image_json, output_path):
    try:
        # Aqui, pegamos a imagem da chave "img_tratada"
        image_data = image_json.get("img_tratada", "")
        
        if not image_data:
            raise ValueError("Imagem não encontrada na chave 'img_tratada' do JSON")

        # Decodificando a imagem Base64
        missing_padding = len(image_data) % 4
        if missing_padding:
            image_data += '=' * (4 - missing_padding)

        with open(output_path, "wb") as output_file:
            output_file.write(base64.b64decode(image_data))

        return True, "Imagem decodificada com sucesso"
    except json.JSONDecodeError as json_err:
        return False, f"Erro ao decodificar JSON: {str(json_err)}"
    except ValueError as val_err:
        return False, str(val_err)
    except Exception as e:
        return False, f"Erro ao decodificar a imagem: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
