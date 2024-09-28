from flask import Flask, request, jsonify
import funcoes.IA_a as IA_a
import os
import datetime
from funcoes.serializador_de_imagem import transforma_imagem_em_json
from firebase import db, bucket
from datetime import timedelta


app = Flask(__name__)

@app.route('/predict/<id_usuario>', methods=['POST'])
def predict(id_usuario):

    # ------------------------- Parte envolvendo receber a imagem e id do usuario da requisição -------------------------

    #espera uma imagem a ser tratada pela IA e um id de usuario na rota
    if not request.files:
        return jsonify({'error': 'Nenhuma imagem provida'}), 400

    imagem = next(iter(request.files.values()))

    image_dir = "IA/img/"
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    #salva o path de onde ficou a imagem
    image_path = os.path.join(image_dir, imagem.filename)
    imagem.save(image_path)

    supported_formats = {'bmp', 'jpg', 'png', 'tiff', 'mpo', 'webp', 'jpeg', 'dng', 'pfm', 'tif'}

    if image_path.split('.')[-1].lower() not in supported_formats:
        os.remove(image_path)
        return jsonify({'error': 'Formato de imagem não suportado'}), 400

    print(f"Imagem encontrada: {image_path}")

    # -------------------------------------------------------------------------------------------------------------------

    # ------------------------------ Parte envolvendo tratar a imagem recebida com a IA ---------------------------------
    
    

    # Aqui estamos garantindo que a função IA retorna três valores
    mask_path, imagem_tratada_pela_IA, porcentagem_nuvem = IA_a.IA(image_path)
    nome_base = os.path.splitext(imagem.filename)[0]

    # Salvar como imagem antes de converter caso queira versão json
    #imagem_original_json = transforma_imagem_em_json(image_path)
    # -------------------------------------------------------------------------------------------------------------------

    # ------------ Parte envolvendo a montagem do JSON para salvar no firebase e devolver a resposta --------------------

    #cria as informações data e horario
    data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
    hora_atual = datetime.datetime.now().strftime("%H:%M:%S")

    # Como `imagem_tratada` é um `numpy.ndarray`, você pode obter a resolução diretamente
    resolucao_da_imagem = f"{imagem_tratada_pela_IA.shape[1]}x{imagem_tratada_pela_IA.shape[0]}"  # largura x altura

    #faz os calculos para ter a porcentagem de nuvem e area visivel
    area_visivel_mapa = 100 - porcentagem_nuvem
    porcentagem_nuvem = round(porcentagem_nuvem, 2)
    area_visivel_mapa = round(area_visivel_mapa, 2)

    # Salvar como imagem antes de converter caso queira versão json
    #imagem_tratada_json = transforma_imagem_em_json('IA/img_mark_e_merged/merged_output_with_color.png')  
    imagem_IA_path = 'IA/img_mark_e_merged/merged_output_with_color.png'

    #acessa a coleção no firebase "historico_imagens_ia"
    collection_ref = db.collection("historico_imagens_ia")

    #abre e faz um count de quantos documentos tem para adicionar no doc_count apenas do id usuario
    docs = collection_ref.where("id_usuario", "==", id_usuario).stream()
    doc_count = sum(1 for _ in docs)

    #cria o campo id unico para o frontend consumir e trazer todas as requisições de um usuario especifico
    id_unico = f"{nome_base}_{doc_count + 1}"

    #versão count todos os documentos
    #docs = collection_ref.stream()
    #doc_count = sum(1 for _ in docs)
    #id_unico = f"{nome_base}_{doc_count}"

    #salva a imagem original e a imagem tratada pela IA no bucket do firebase, referenciando caminhos no bucket
    blob = bucket.blob(f"imagens/original/{nome_base}_{doc_count}")
    #pega o path das imagens e salva elas
    blob.upload_from_filename(image_path)
    #tira o tempo de expiração
    blob.make_public()
    #retorna a url da imagem salva para ser salva no json do firestorm e devolvida na resposta
    imagem_original_url = blob.public_url

    #mesma lógica que os comentários de cima
    blob = bucket.blob(f"imagens/tratada/{nome_base}_{doc_count}")
    blob.upload_from_filename(imagem_IA_path)
    blob.make_public()
    imagem_tratada_pela_IA_url = blob.public_url


    #salva no firestorm o json que o frontend precisa consumir
    collection_ref = db.collection("historico_imagens_ia")
    collection_ref.add({
        "id_usuario": id_usuario,
        "id": id_unico,
        "data": data_atual,
        "hora": hora_atual,
        "geometry": {
            "type": "Polygon",
            "coordinates": None
        },
        "resolucao_imagem": resolucao_da_imagem,
        "satelite": "CBERS4A",
        "sensor": "WPM",
        "percentual_nuvem": porcentagem_nuvem,
        "area_visivel_mapa": area_visivel_mapa,
        "imagem": None,
        "thumbnail": imagem_original_url,
        "img_tratada": imagem_tratada_pela_IA_url
    })


    # Apaga a imagem da pasta local após termino da utilidade dela, para que não encha a pasta IA/img
    for file in os.listdir(image_dir):
        if file.split('.')[-1].lower() in supported_formats:
            file_path = os.path.join(image_dir, file)
            os.remove(file_path)

    resposta = {
        "id_usuario": id_usuario,
        "id": id_unico,
        "data": data_atual,
        "hora": hora_atual,
        "geometry": {
            "type": "Polygon",
            "coordinates": None
        },
        "resolucao_imagem": resolucao_da_imagem,
        "satelite": "CBERS4A",
        "sensor": "WPM",
        "percentual_nuvem": porcentagem_nuvem,
        "area_visivel_mapa": area_visivel_mapa,
        "imagem": None,
        "thumbnail": imagem_original_url,
        "img_tratada": imagem_tratada_pela_IA_url
    }

    return jsonify(resposta)

@app.route('/historico/<id_usuario>', methods=['GET'])
def get_historico(id_usuario):
    collection_ref = db.collection("historico_imagens_ia")
    
    # Recuperando os documentos que têm o campo "id_usuario" igual ao valor passado
    documentos = collection_ref.where("id_usuario", "==", id_usuario).stream()
    
    # Criando uma lista para armazenar os dados
    historico = []
    
    for doc in documentos:
        # Adicionando os dados de cada documento à lista
        historico.append(doc.to_dict())
    
    # Retornando os dados em formato JSON
    return jsonify(historico)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
