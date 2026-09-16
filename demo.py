import sys
import cv2
import pygame
import numpy as np

# --- Konfigurasi ---
CAM_INDEX = 0          # ganti jika webcam ada di index lain
WINDOW_TITLE = "Demo Pygame + OpenCV - Face Detection"

def main():
    # --- Inisialisasi OpenCV ---
    cap = cv2.VideoCapture(CAM_INDEX)
    if not cap.isOpened():
        print("Tidak bisa membuka webcam. Cek CAM_INDEX atau koneksi kamera.")
        sys.exit(1)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    ret, frame = cap.read()
    if not ret:
        print("Gagal membaca frame pertama dari webcam.")
        sys.exit(1)

    frame_h, frame_w = frame.shape[:2]

    # --- Inisialisasi Pygame ---
    pygame.init()
    screen = pygame.display.set_mode((frame_w, frame_h))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)

    running = True
    while running:
        # --- Event handling Pygame ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # --- Ambil frame dari webcam (OpenCV) ---
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)  # mirror biar seperti cermin

        # --- Deteksi wajah dengan OpenCV ---
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # --- Konversi frame OpenCV (BGR) -> Pygame surface (RGB) ---
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = np.rot90(frame_rgb)          # sesuaikan orientasi
        surface = pygame.surfarray.make_surface(frame_rgb)
        surface = pygame.transform.flip(surface, True, False)

        # --- Render ke window Pygame ---
        screen.blit(surface, (0, 0))

        info_text = font.render(
            f"Wajah terdeteksi: {len(faces)}  |  ESC untuk keluar",
            True, (255, 255, 0)
        )
        screen.blit(info_text, (10, 10))

        pygame.display.flip()
        clock.tick(30)  # batasi 30 FPS

    cap.release()
    pygame.quit()


if __name__ == "__main__":
    main()