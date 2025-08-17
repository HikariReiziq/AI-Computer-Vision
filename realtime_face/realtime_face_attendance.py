import cv2
import face_recognition
import os
import pandas as pd
from datetime import datetime
from deepface import DeepFace

# Folder berisi foto orang yang dikenal
KNOWN_FACES_DIR = "dataset"
ATTENDANCE_FILE = "attendance.csv"

# Load known faces
known_encodings = []
known_names = []

for filename in os.listdir(KNOWN_FACES_DIR):
    if filename.endswith((".jpg", ".png")):
        img = face_recognition.load_image_file(os.path.join(KNOWN_FACES_DIR, filename))
        enc = face_recognition.face_encodings(img)[0]
        known_encodings.append(enc)
        known_names.append(os.path.splitext(filename)[0])

# Buat file absensi kalau belum ada
if not os.path.exists(ATTENDANCE_FILE):
    df = pd.DataFrame(columns=["Name", "Date", "Time", "Emotion"])
    df.to_csv(ATTENDANCE_FILE, index=False)

def mark_attendance(name, emotion):
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    df = pd.read_csv(ATTENDANCE_FILE)
    # Cek apakah sudah absen hari ini
    if not ((df["Name"] == name) & (df["Date"] == date)).any():
        new_data = {"Name": name, "Date": date, "Time": time, "Emotion": emotion}
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        df.to_csv(ATTENDANCE_FILE, index=False)
        print(f"[INFO] {name} tercatat hadir ({emotion})")

# Mulai kamera
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    locations = face_recognition.face_locations(rgb)
    encodings = face_recognition.face_encodings(rgb, locations)

    for (top, right, bottom, left), face_encoding in zip(locations, encodings):
        matches = face_recognition.compare_faces(known_encodings, face_encoding)
        name = "Unknown"

        if True in matches:
            first_match_index = matches.index(True)
            name = known_names[first_match_index]

            # Crop wajah untuk analisis emosi
            face_crop = frame[top:bottom, left:right]
            try:
                result = DeepFace.analyze(face_crop, actions=['emotion'], enforce_detection=False)
                emotion = result[0]['dominant_emotion']
            except:
                emotion = "N/A"

            # Tandai kehadiran
            mark_attendance(name, emotion)
        else:
            emotion = "N/A"

        # Gambar kotak + nama + emosi
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, f"{name} ({emotion})", (left, top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow("Attendance + Emotion Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
