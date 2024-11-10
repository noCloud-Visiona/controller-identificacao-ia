import os
import cv2
import requests
import datetime
import rasterio
from rasterio.windows import from_bounds
from pyproj import Transformer 
from services import baixar_imagem, validar_formato_imagem
from services import montar_json_response, processar_imagem_com_ia, enviar_json_final

def processar_imagem(band16_url, image_dir, json_data, job_id, processing_jobs, id_usuario):
    """
    Função para processar a imagem em segundo plano e enviar o resultado ao frontend.
    """
    try:
        print("Iniciando o processo de imagem...")
        
        # Baixar a imagem
        print("Baixando a imagem...")
        image_path = baixar_imagem(band16_url, image_dir=image_dir)
        validar_formato_imagem(image_path)
        print(f"Imagem baixada: {image_path}")

        # Obter a área de recorte (bbox) do JSON de entrada
        bbox = json_data.get('bbox')
        if not bbox:
            raise ValueError("A área de recorte 'bbox' não foi especificada no JSON de entrada.")
        
        # Extrair as coordenadas geográficas (latitude e longitude) da bounding box
        minx, miny, maxx, maxy = bbox
        print(f"Coordenadas da bbox recebidas: minx={minx}, miny={miny}, maxx={maxx}, maxy={maxy}")

        # Configurar a conversão de coordenadas de WGS84 para UTM (EPSG:32723)
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:32723", always_xy=True)
        minx_utm, miny_utm = transformer.transform(minx, miny)
        maxx_utm, maxy_utm = transformer.transform(maxx, maxy)
        print(f"Coordenadas bbox convertidas para UTM: minx_utm={minx_utm}, miny_utm={miny_utm}, maxx_utm={maxx_utm}, maxy_utm={maxy_utm}")

        # Abrir a imagem e verificar os limites
        with rasterio.open(image_path) as src:
            print(f"Sistema de coordenadas da imagem: {src.crs}")
            print(f"Limites da imagem: {src.bounds}")
            
            # Verificar se as coordenadas estão dentro dos limites da imagem
            if (minx_utm < src.bounds.left or maxx_utm > src.bounds.right or
                miny_utm < src.bounds.bottom or maxy_utm > src.bounds.top):
                raise ValueError("As coordenadas do bbox estão fora dos limites da imagem.")
            
            # Converte as coordenadas geográficas para a janela de pixels correspondente
            print("Calculando a janela de corte...")
            window = from_bounds(minx_utm, miny_utm, maxx_utm, maxy_utm, src.transform)
            profile = src.profile  # Copia o perfil da imagem original
            print(f"Dimensões da janela de corte: largura={window.width}, altura={window.height}")

            # Atualiza o perfil para o novo tamanho
            profile.update(
                width=window.width,
                height=window.height,
                transform=rasterio.windows.transform(window, src.transform)
            )

            # Cria um novo arquivo recortado temporário com base na bbox
            cropped_image_path = os.path.join(os.path.dirname(image_path), "cropped_image.tif").replace("\\", "/")
            print(f"Salvando a imagem recortada em: {cropped_image_path}")


            # Salva a imagem recortada
            with rasterio.open(cropped_image_path, "w", **profile) as dst:
                for i in range(1, src.count + 1):
                    print(f"Processando banda {i}/{src.count}")
                    dst.write(src.read(i, window=window), i)
            print("Imagem recortada salva com sucesso.")

        # -------------------- Processamento da imagem --------------------
        print("Iniciando o processamento da imagem com IA...")
        mask_path, caminho_imagem_tratada, porcentagem_nuvem, imagem_tratada = processar_imagem_com_ia(cropped_image_path)
        print("Processamento concluído.")

        # ------------------ Obter informações e compilar resposta ------------------
        data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
        hora_atual = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"Data atual: {data_atual}, Hora atual: {hora_atual}")

        # --------------- Enviar imagens para o bucket e obter URLs ---------------
        print("Enviando imagens processadas para o bucket...")
        with open(caminho_imagem_tratada, 'rb') as tratada_image, open(mask_path, 'rb') as nuvem_image:
            files = {'tratada': tratada_image, 'nuvem': nuvem_image}
            response_tratada = requests.post('http://host.docker.internal:3004/upload_image_tratada_png', files={'tratada': files['tratada']})
            tratada_url = response_tratada.json().get('url')  # Supondo que a resposta contenha a URL
            print(f"URL da imagem tratada: {tratada_url}")

        # Montar o JSON final para enviar ao frontend
        json_response = montar_json_response(
            json_data,
            mask_path,
            caminho_imagem_tratada,
            porcentagem_nuvem,
            imagem_tratada,
            tratada_url,
            mask_path,
            data_atual,
            hora_atual,
            id_usuario
        )
        print(f"JSON final montado: {json_response}")
        processing_jobs[job_id]["status"] = "Análise concluída!"
        processing_jobs[job_id]["result"] = json_response  # O resultado que você deseja retornar

    except Exception as e:
        print(f"Erro: {str(e)}")
        processing_jobs[job_id]["status"] = "Ops... Algo de errado aconteceu!"
        processing_jobs[job_id]["result"] = str(e)
