"""
Realtime webcam demo with OpenCV DNN Face Detector (Python 3.13 compatible)

Fitur:
- Menampilkan frame dari webcam
- Deteksi wajah dengan DNN (lebih akurat daripada Haar Cascade)
- FPS counter
- Toggle grayscale / Canny edge
- Tekan 's' untuk simpan frame, 'q' untuk keluar
"""

import cv2
import time
import os

def ensure_out_dir(path="captures"):
    os.makedirs(path, exist_ok=True)
    return path

def main(camera_index=0):
    out_dir = ensure_out_dir()

    # Load model DNN (pastikan file ada di folder "models/")
    proto = "models/deploy.prototxt"
    model = "models/res10_300x300_ssd_iter_140000.caffemodel"
    net = cv2.dnn.readNetFromCaffe(proto, model)

    cap = cv2.VideoCapture(camera_index, cv2.CAP_ANY)
    if not cap.isOpened():
        print(f"[ERROR] Tidak bisa membuka kamera index {camera_index}.")
        return

    prev_time = time.time()
    fps = 0.0
    show_gray = False
    show_canny = False
    frame_counter = 0

    print("Tekan 'q' untuk keluar, 's' untuk simpan frame, 'g' toggle grayscale, 'c' toggle Canny edges.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Gagal membaca frame dari kamera.")
            break

        frame_counter += 1
        curr_time = time.time()
        dt = curr_time - prev_time
        if dt >= 0.2:
            fps = 1.0 / dt
            prev_time = curr_time

        display = frame.copy()

        # Pilihan mode tampilan
        if show_gray:
            display = cv2.cvtColor(display, cv2.COLOR_BGR2GRAY)
            display = cv2.cvtColor(display, cv2.COLOR_GRAY2BGR)
        if show_canny:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            display = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        # DNN Face Detection
        (h, w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
                                     (300, 300), (104.0, 177.0, 123.0))
        net.setInput(blob)
        detections = net.forward()

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:  # threshold deteksi
                box = detections[0, 0, i, 3:7] * [w, h, w, h]
                (x1, y1, x2, y2) = box.astype("int")
                cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(display, f"Wajah {confidence*100:.1f}%", 
                            (x1, y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

        # Overlay teks
        cv2.putText(display, f"FPS: {fps:.1f}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
        mode = "GRAY" if show_gray else "COLOR"
        if show_canny:
            mode = "CANNY"
        cv2.putText(display, f"Mode: {mode}", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,0), 2)

        cv2.imshow("Realtime DNN Face Detector", display)

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
    main(camera_index=0)
