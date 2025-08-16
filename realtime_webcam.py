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
        if show_gray:
            display = cv2.cvtColor(display, cv2.COLOR_BGR2GRAY)
            display = cv2.cvtColor(display, cv2.COLOR_GRAY2BGR)  # buat konsisten 3-channel untuk drawing
        if show_canny:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            display = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        # Deteksi wajah (selalu gunakan frame berwarna abu-abu untuk deteksi)
        try:
            gray_for_detect = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray_for_detect, scaleFactor=1.1, minNeighbors=5, minSize=(40,40))
        except Exception:
            faces = []

        # Gambar kotak pada wajah
        for (x, y, w, h) in faces:
            cv2.rectangle(display, (x,y), (x+w, y+h), (0,255,0), 2)
            cv2.putText(display, "Wajah", (x, y-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

        # Overlay teks FPS dan instruksi
        cv2.putText(display, f"FPS: {fps:.1f}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        mode = "GRAY" if show_gray else "COLOR"
        if show_canny:
            mode = "CANNY"
        cv2.putText(display, f"Mode: {mode}", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)

        # Tampilkan
        cv2.imshow("Realtime CV Demo", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = os.path.join(out_dir, f"frame_{int(time.time())}.png")
            cv2.imwrite(filename, display)
            print(f"[SAVED] {filename}")
        elif key == ord('g'):
            show_gray = not show_gray
        elif key == ord('c'):
            show_canny = not show_canny

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    # Jika mau gunakan camera index lain, ubah argumen di main()
    main(camera_index=0)
