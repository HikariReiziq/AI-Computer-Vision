#!/usr/bin/env python3
"""
Realtime webcam demo with OpenCV (Python 3.13 compatible)

Fitur:
- Menampilkan frame dari webcam
- Deteksi wajah (Haar Cascade) dan gambar kotak pada wajah
- FPS counter
- Toggle grayscale / Canny edge
- Tekan 's' untuk menyimpan frame, 'q' untuk keluar

Jalankan: python realtime_webcam_cv.py
"""
import cv2
import time
import os

def ensure_out_dir(path="captures"):
    os.makedirs(path, exist_ok=True)
    return path

def main(camera_index=0):
    out_dir = ensure_out_dir()

    # Buka webcam (0 = default). Jika punya device lain, ubah index.
    cap = cv2.VideoCapture(camera_index, cv2.CAP_ANY)

    if not cap.isOpened():
        print(f"[ERROR] Tidak bisa membuka kamera index {camera_index}. Coba cek koneksi / index kamera.")
        return

    # Gunakan Haar cascade yang ada di instalasi opencv-python
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        print("[WARNING] Gagal load haarcascade. Deteksi wajah tidak akan bekerja.")

    prev_time = time.time()
    fps = 0.0
    show_gray = False
    show_canny = False
    frame_counter = 0

    print("Tekan 'q' untuk keluar, 's' untuk simpan frame, 'g' toggle grayscale, 'c' toggle Canny edges.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Gagal membaca frame dari kamera. Mengakhiri...")
            break

        frame_counter += 1

        # Hitung FPS sederhana (running)
        curr_time = time.time()
        dt = curr_time - prev_time
        if dt >= 0.2:
            fps = 1.0 / dt
            prev_time = curr_time

        display = frame.copy()

        # Pilihan mode tampilan
        

if __name__ == "__main__":
    # Jika mau gunakan camera index lain, ubah argumen di main()
    main(camera_index=0)
