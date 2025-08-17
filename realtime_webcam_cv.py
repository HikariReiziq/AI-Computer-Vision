import cv2
import numpy as np
import os
import urllib.request

def download_models(model_dir="models"):
    """
    Download model DNN (Caffe) untuk deteksi wajah
    jika belum tersedia di folder.
    """
    os.makedirs(model_dir, exist_ok=True)

    files = {
        "deploy.prototxt": "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt",
        "res10_300x300_ssd_iter_140000.caffemodel": "https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
    }

    for filename, url in files.items():
        path = os.path.join(model_dir, filename)
        if not os.path.exists(path):
            print(f"[INFO] Downloading {filename} ...")
            urllib.request.urlretrieve(url, path)
            print(f"[OK] {filename} saved to {path}")
        else:
            print(f"[SKIP] {filename} already exists.")


def main(camera_index=0):
    # Pastikan model sudah ada
    download_models("models")

    # Load model
    proto = "models/deploy.prototxt"
    model = "models/res10_300x300_ssd_iter_140000.caffemodel"
    net = cv2.dnn.readNetFromCaffe(proto, model)

    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print("[ERROR] Tidak bisa membuka kamera")
        return

    print("[INFO] Tekan 'q' untuk keluar.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Gagal membaca frame dari kamera")
            break

        (h, w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
                                     (300, 300), (104.0, 177.0, 123.0))
        net.setInput(blob)
        detections = net.forward()

        for i in range(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            if confidence > 0.5:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                text = f"{confidence*100:.2f}%"
                y = startY - 10 if startY - 10 > 10 else startY + 10

                cv2.rectangle(frame, (startX, startY), (endX, endY),
                              (0, 255, 0), 2)
                cv2.putText(frame, text, (startX, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 2)

        cv2.imshow("Real-Time Face Detection (DNN)", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main(camera_index=0)
