import cv2

def tratar_imagem(image):
    original_img = cv2.imread(image)

    resized_img = cv2.resize(original_img, (640, 640))

    # Converter a imagem para tons de cinza
    gray_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)

    # Converter de volta para 3 canais
    gray_img_3ch = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)
    return gray_img_3ch

def tratar_imagem_cinza(image):
    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray_img_3ch = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)

    return gray_img_3ch