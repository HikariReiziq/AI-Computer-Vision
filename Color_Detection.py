import cv2
import numpy as np

# Fungsi untuk mendeteksi warna dan akurasi
def detect_color(hsv_pixel):
    colors = {
        'Merah': ([0, 70, 50], [10, 255, 255]),
        'Kuning': ([20, 100, 100], [30, 255, 255]),
        'Hijau': ([40, 40, 40], [80, 255, 255]),
        'Biru': ([90, 50, 50], [130, 255, 255]),
        'Putih': ([0, 0, 200], [180, 25, 255]),
        'Hitam': ([0, 0, 0], [180, 255, 30])
    }

    for name, (lower, upper) in colors.items():
        lower_np = np.array(lower)
        upper_np = np.array(upper)
        if np.all(hsv_pixel >= lower_np) and np.all(hsv_pixel <= upper_np):
            center = (lower_np + upper_np) / 2
            dist = np.linalg.norm(hsv_pixel - center)
            max_dist = np.linalg.norm(upper_np - lower_np) / 2
            accuracy = max(0, 100 - (dist / max_dist * 100))
            return name, round(accuracy, 1), lower_np, upper_np
    return "Tidak Dikenal", 0, None, None

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Loop semua warna yang didefinisikan
    for color_name, (lower, upper) in {
        'Merah': ([0, 70, 50], [10, 255, 255]),
        'Kuning': ([20, 100, 100], [30, 255, 255]),
        'Hijau': ([40, 40, 40], [80, 255, 255]),
        'Biru': ([90, 50, 50], [130, 255, 255]),
        'Putih': ([0, 0, 200], [180, 25, 255]),
        'Hitam': ([0, 0, 0], [180, 255, 30])
    }.items():
        lower_np = np.array(lower)
        upper_np = np.array(upper)
        mask = cv2.inRange(hsv_frame, lower_np, upper_np)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if cv2.contourArea(contour) > 500:
                x, y, w, h = cv2.boundingRect(contour)
                # Ambil warna di tengah bounding box untuk akurasi
                hsv_pixel = hsv_frame[y + h // 2, x + w // 2]
                _, accuracy, _, _ = detect_color(hsv_pixel)

                # Gambar kotak dan teks
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"{color_name} - {accuracy}%", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    cv2.imshow('Color Object Detection', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
