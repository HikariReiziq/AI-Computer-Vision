import cv2
import os
import pandas as pd
from datetime import datetime
from deepface import DeepFace

ATTENDANCE_FILE = "attendance.csv"
FACE_DIR = "faces"


def mark_attendance(name, emotion):
    if not os.path.exists(ATTENDANCE_FILE):
        df = pd.DataFrame(columns=["Name", "Emotion", "Time"])
        df.to_csv(ATTENDANCE_FILE, index=False)

    df = pd.read_csv(ATTENDANCE_FILE)
    if name not in df["Name"].values:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_entry = {"Name": name, "Emotion": emotion, "Time": now}
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(ATTENDANCE_FILE, index=False)
        print(f"[LOG] Attendance: {name} - {emotion} - {now}")

def register_face():
    name = input("Masukkan nama Anda: ").strip()
    save_path = os.path.join(FACE_DIR, f"{name}.jpg")

    cap = cv2.VideoCapture(0)
    print("[INFO] Tekan 's' untuk simpan wajah, 'q' untuk keluar")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow("Register Face", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("s"):
            cv2.imwrite(save_path, frame)
            print(f"[SAVED] Wajah {name} tersimpan di {save_path}")
            break
        elif key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

def attendance_mode():
    cap = cv2.VideoCapture(0)
    print("[INFO] Tekan 'q' untuk keluar")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        try:
            results = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=False)
            if not isinstance(results, list):
                results = [results]

            for res in results:
                x, y, w, h = res["region"].values()
                dominant_emotion = res["dominant_emotion"]

                # Default jika tidak cocok
                name = "Unknown"

                # Coba cocokkan dengan semua wajah di database
                for file in os.listdir(FACE_DIR):
                    db_face = os.path.join(FACE_DIR, file)
                    try:
                        verify = DeepFace.verify(frame, db_face, enforce_detection=False)
                        if verify["verified"]:
                            name = os.path.splitext(file)[0]
                            break
                    except:
                        continue

                mark_attendance(name, dominant_emotion)

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"{name} - {dominant_emotion}", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        except Exception as e:
            print("[INFO] Tidak ada wajah:", e)

        cv2.imshow("Attendance Mode", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    print("1. Register Face")
    print("2. Attendance Mode")
    choice = input("Pilih mode (1/2): ").strip()

    if choice == "1":
        register_face()
    elif choice == "2":
        attendance_mode()
    else:
        print("Pilihan tidak valid.")
