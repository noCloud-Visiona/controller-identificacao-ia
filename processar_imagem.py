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
    try:
        print("[INFO] Iniciando o processo de imagem...")

        # Baixar a imagem
        print("[INFO] Baixando a imagem...")
        image_path = baixar_imagem(band16_url, image_dir=image_dir)
        validar_formato_imagem(image_path)
        print(f"[INFO] Imagem baixada com sucesso: {image_path}")

        # Priorizar user_geometry se disponível
        user_geometry = json_data.get('user_geometry')
        if user_geometry:
            print(f"[INFO] Usando user_geometry para o recorte: {user_geometry}")
            coordinates = user_geometry['coordinates'][0]
            minx, miny = coordinates[0]
            maxx, maxy = coordinates[2]
        else:
            print("[INFO] user_geometry não encontrado. Usando bbox padrão.")
            bbox = json_data.get('bbox')
            if not bbox:
                raise ValueError("A área de recorte 'bbox' não foi especificada no JSON de entrada.")
            minx, miny, maxx, maxy = bbox

        print(f"[INFO] Coordenadas de recorte: minx={minx}, miny={miny}, maxx={maxx}, maxy={maxy}")

        # Conversão de coordenadas WGS84 para UTM
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:32723", always_xy=True)
        minx_utm, miny_utm = transformer.transform(minx, miny)
        maxx_utm, maxy_utm = transformer.transform(maxx, maxy)
        print(f"[INFO] Coordenadas bbox convertidas para UTM: minx_utm={minx_utm}, miny_utm={miny_utm}, maxx_utm={maxx_utm}, maxy_utm={maxy_utm}")

        # Abrir a imagem e verificar os limites
        with rasterio.open(image_path) as src:
            print(f"[INFO] Sistema de coordenadas da imagem: {src.crs}")
            print(f"[INFO] Limites da imagem: {src.bounds}")

            # Verificar se as coordenadas estão dentro dos limites da imagem
            if (minx_utm < src.bounds.left or maxx_utm > src.bounds.right or
                miny_utm < src.bounds.bottom or maxy_utm > src.bounds.top):
                raise ValueError("[ERRO] As coordenadas do bbox estão fora dos limites da imagem.")

            # Calcular a janela de corte
            print("[INFO] Calculando a janela de corte...")
            window = from_bounds(minx_utm, miny_utm, maxx_utm, maxy_utm, src.transform)
            profile = src.profile  # Copiar o perfil da imagem original
            print(f"[INFO] Dimensões da janela de corte: largura={window.width}, altura={window.height}")

            # Atualizar o perfil para o novo tamanho
            profile.update(
                width=window.width,
                height=window.height,
                transform=rasterio.windows.transform(window, src.transform)
            )

            # Criar um arquivo recortado temporário
            cropped_image_path = os.path.join(os.path.dirname(image_path), "cropped_image.tif").replace("\\", "/")
            print(f"[INFO] Salvando a imagem recortada em: {cropped_image_path}")

            with rasterio.open(cropped_image_path, "w", **profile) as dst:
                for i in range(1, src.count + 1):
                    print(f"[INFO] Processando banda {i}/{src.count}")
                    dst.write(src.read(i, window=window), i)
            print("[INFO] Imagem recortada salva com sucesso.")

        # Processar a imagem recortada
        print("[INFO] Iniciando o processamento da imagem com IA...")
        mask_path, caminho_imagem_tratada, porcentagem_nuvem, imagem_tratada = processar_imagem_com_ia(cropped_image_path)
        print("[INFO] Processamento concluído.")

        # Obter informações de data e hora
        data_atual = datetime.datetime.now().strftime("%Y-%m-%d")
        hora_atual = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[INFO] Data atual: {data_atual}, Hora atual: {hora_atual}")

        # Enviar imagens para o bucket e obter URLs
        print("[INFO] Enviando imagens processadas para o bucket...")
        with open(caminho_imagem_tratada, 'rb') as tratada_image, open(mask_path, 'rb') as nuvem_image:
            files = {'tratada': tratada_image, 'nuvem': nuvem_image}
            response_tratada = requests.post('http://host.docker.internal:3004/upload_image_tratada_png', files={'tratada': files['tratada']})
            tratada_url = response_tratada.json().get('url')
            print(f"[INFO] URL da imagem tratada: {tratada_url}")

        # Montar o JSON final
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
        print(f"[INFO] JSON final montado: {json_response}")
        processing_jobs[job_id]["status"] = "Análise concluída!"
        processing_jobs[job_id]["result"] = json_response

    except Exception as e:
        print(f"[ERRO] {str(e)}")
        processing_jobs[job_id]["status"] = "Ops... Algo de errado aconteceu!"
        processing_jobs[job_id]["result"] = str(e)
