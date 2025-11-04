import cv2
import numpy as np

# --- 1. Carregar a Imagem de Referência (Template) ---
TEMPLATE_PATH = "bomba_mario.png" 

template = cv2.imread(TEMPLATE_PATH, cv2.IMREAD_GRAYSCALE)
if template is None:
    print(f"Erro: Não foi possível carregar a imagem de template em '{TEMPLATE_PATH}'.")
    print("Verifique o caminho e o nome do arquivo.")
    exit()

# --- 2. Inicializar o Detector de Características (SIFT) ---
try:
    sift = cv2.SIFT_create()
except cv2.error as e:
    print("Erro ao inicializar o SIFT. Você instalou o 'opencv-contrib-python'?")
    print("Execute: pip uninstall opencv-python")
    print("Depois:   pip install opencv-contrib-python")
    exit()


# Encontra os pontos chave (keypoints) e descritores do template
kp_template, des_template = sift.detectAndCompute(template, None)

if des_template is None:
    print("Não foram encontrados pontos de característica suficientes no template.")
    print("Tente uma imagem de template com mais detalhes.")
    exit()

# --- 3. Configurar o Matcher (FLANN) ---
FLANN_INDEX_KDTREE = 1
index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
search_params = dict(checks=50) 

flann = cv2.FlannBasedMatcher(index_params, search_params)

# --- 4. Configura a Captura de Vídeo do MJPEG ---
stream_url = "http://pizero.local:8000/stream.mjpg" 
cap = cv2.VideoCapture(stream_url)
if not cap.isOpened():
    print("Erro: Não foi possível abrir a câmera.")
    exit()

print(f"\nProcurando a imagem '{TEMPLATE_PATH}' (usando SIFT). Pressione 'q' para sair.")

# --- 5. Loop Principal de Processamento ---
while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, -1)
    if not ret:
        print("Erro: Não foi possível ler o frame.")
        break

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Encontra os keypoints e descritores do frame atual
    kp_frame, des_frame = sift.detectAndCompute(gray_frame, None)

    img_center_x = None
    img_center_y = None

    if des_frame is not None and len(des_frame) > 2:
        # Usa knnMatch (k=2) para encontrar os 2 vizinhos mais próximos
        matches = flann.knnMatch(des_template, des_frame, k=2)

        # --- 6. Filtragem (Lowe's Ratio Test) ---
        good_matches = []
        for m, n in matches:
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)

        # --- 7. Localização (Homografia) ---
        MIN_MATCH_COUNT = 15

        if len(good_matches) > MIN_MATCH_COUNT:
            src_pts = np.float32([kp_template[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp_frame[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

            M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 4.0)

            if M is not None:
                h, w = template.shape
                pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
                dst = cv2.perspectiveTransform(pts, M)

                frame = cv2.polylines(frame, [np.int32(dst)], True, (0, 255, 0), 3, cv2.LINE_AA)
                
                x_coords = [p[0][0] for p in dst]
                y_coords = [p[0][1] for p in dst]
                img_center_x = int(np.mean(x_coords))
                img_center_y = int(np.mean(y_coords))
                
                cv2.circle(frame, (img_center_x, img_center_y), 5, (0, 0, 255), -1)

    # --- 8. Lógica de Alerta ---
    if img_center_x is not None:
        comando = "ALERTA: BOMBA DETECTADA!"
        cv2.putText(frame, comando, (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    else:
        cv2.putText(frame, "Procurando...", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 100, 0), 2)

    # --- 9. Exibição ---
    cv2.imshow("Frame com Deteccao (SIFT)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- 10. Limpeza ---
print("Encerrando...")
cap.release()
cv2.destroyAllWindows()
