import os
import cv2
import requests
import datetime
from services import montar_json_response, processar_imagem_com_ia, enviar_json_final

def processar_imagem(image_path, json_data, job_id, processing_jobs, id_usuario):
    """
    Função para processar a imagem em segundo plano e enviar o resultado ao frontend.
    """
    try:
        # -------------------- Processamento da imagem --------------------
        mask_path, caminho_imagem_tratada, porcentagem_nuvem, imagem_tratada = processar_imagem_com_ia(image_path)
        
        # ------------------ Obter informações e compilar resposta ------------------
        data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
        hora_atual = datetime.datetime.now().strftime("%H:%M:%S")

        # --------------- Enviar imagens para o bucket e obter URLs ---------------
        with open(caminho_imagem_tratada, 'rb') as tratada_image, open(mask_path, 'rb') as nuvem_image:
            files = {'tratada': tratada_image, 'nuvem': nuvem_image}
            response_tratada = requests.post('http://host.docker.internal:3004/upload_image_tratada_png', files={'tratada': files['tratada']})
            tratada_url = response_tratada.json().get('url')  # Supondo que a resposta contenha a URL
            # Aqui você deve tratar a resposta para obter a URL correta

        # Montar o JSON final para enviar ao frontend
        json_response = montar_json_response(
            json_data,
            mask_path,
            caminho_imagem_tratada,
            porcentagem_nuvem,
            imagem_tratada,
            tratada_url,
            mask_path,  # ou a URL correta para a máscara
            data_atual,
            hora_atual,
            id_usuario
        )
        
        processing_jobs[job_id]["status"] = "Análise concluída!"
        processing_jobs[job_id]["result"] = json_response  # O resultado que você deseja retornar
    except Exception as e:
        processing_jobs[job_id]["status"] = "Ops... Algo de errado aconteceu!"
        processing_jobs[job_id]["result"] = str(e)