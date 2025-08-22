import cv2
import numpy as np
import time
from collections import defaultdict
from typing import List, Tuple, Dict

# DeepFace: model emosi siap pakai
from deepface import DeepFace

# ----------------------------
# Konfigurasi
# ----------------------------
CFG = {
    "camera_index": 0,
    "width": 1280,
    "height": 720,
    "frame_stride": 2,          # Analisis tiap N frame untuk hemat compute
    "ema_alpha": 0.7,           # 0.0 = halus banget, 1.0 = sangat responsif
    "min_iou_match": 0.3,       # Ambang IOU untuk match deteksi ke track lama
    "detector_backend": "mediapipe",  # backend deteksi wajah di DeepFace
    "align": True,
    "draw_bars": True,
    "topk": 2                   # tampilkan Top-K emosi
}

# Mapping warna per emosi
EMO_COLORS = {
    "happy":   (40, 200, 40),
    "sad":     (200, 120, 40),
    "angry":   (50, 50, 230),
    "surprise":(40, 180, 240),
    "fear":    (180, 100, 200),
    "disgust": (0, 180, 120),
    "neutral": (200, 200, 200)
}

# Emoji sederhana per emosi (bisa diganti gambar PNG jika mau)
EMO_EMOJI = {
    "happy": "😄",
    "sad": "😢",
    "angry": "😠",
    "surprise": "😮",
    "fear": "😨",
    "disgust": "🤢",
    "neutral": "😐"
}

# ----------------------------
# Utilitas
# ----------------------------
def iou(boxA, boxB) -> float:
    # box: [x, y, w, h]
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = interW * interH
    boxAArea = boxA[2] * boxA[3]
    boxBArea = boxB[2] * boxB[3]
    denom = float(boxAArea + boxBArea - interArea + 1e-6)
    return interArea / denom

def ensure_list(result):
    # DeepFace.analyze kadang mengembalikan dict tunggal atau list
    if isinstance(result, list):
        return result
    return [result]

def softmax(d: Dict[str, float]) -> Dict[str, float]:
    # Normalisasi jika belum
    vals = np.array(list(d.values()), dtype=np.float32)
    e = np.exp(vals - vals.max())
    p = (e / e.sum()).tolist()
    return {k: v for k, v in zip(d.keys(), p)}

def topk_items(prob: Dict[str, float], k: int = 2) -> List[Tuple[str, float]]:
    return sorted(prob.items(), key=lambda x: x[1], reverse=True)[:k]

# ----------------------------
# Pelacakan dan Smoothing
# ----------------------------
class TrackManager:
    def __init__(self, min_iou=0.3, alpha=0.7):
        self.next_id = 1
        self.tracks = {}  # id -> {"box": [x,y,w,h], "prob": {emo: p}, "last_t": t}
        self.min_iou = min_iou
        self.alpha = alpha

    def match_and_update(self, dets: List[Dict], t_now: float):
        # dets: list of {"box":[x,y,w,h], "prob":{emo:p}}
        assigned = set()
        updates = {}

        # Attempt greedy matching by IOU
        for det in dets:
            best_iou, best_id = 0.0, None
            for tid, tr in self.tracks.items():
                i = iou(det["box"], tr["box"])
                if i > best_iou and i >= self.min_iou and tid not in assigned:
                    best_iou, best_id = i, tid

            if best_id is None:
                # New track
                tid = self.next_id
                self.next_id += 1
                smoothed = det["prob"]  # first assignment
                self.tracks[tid] = {"box": det["box"], "prob": smoothed, "last_t": t_now}
                assigned.add(tid)
                updates[tid] = self.tracks[tid]
            else:
                # EMA smoothing
                old_prob = self.tracks[best_id]["prob"]
                new_prob = {}
                for k in set(list(old_prob.keys()) + list(det["prob"].keys())):
                    p_old = old_prob.get(k, 0.0)
                    p_new = det["prob"].get(k, 0.0)
                    new_prob[k] = self.alpha * p_old + (1.0 - self.alpha) * p_new
                # Update
                self.tracks[best_id]["prob"] = new_prob
                self.tracks[best_id]["box"] = det["box"]
                self.tracks[best_id]["last_t"] = t_now
                assigned.add(best_id)
                updates[best_id] = self.tracks[best_id]

        # Optional: hapus track yang tidak terlihat lama (contoh 2 detik)
        to_delete = []
        for tid, tr in self.tracks.items():
            if t_now - tr["last_t"] > 2.0:
                to_delete.append(tid)
        for tid in to_delete:
            del self.tracks[tid]

        return updates  # id->state

# ----------------------------
# Visualisasi
# ----------------------------
def draw_emotion_overlay(
    frame, tid: int, box: List[int], prob: Dict[str, float], topk: int = 2, draw_bars: bool = True
):
    x, y, w, h = box
    x1, y1 = int(x), int(y)
    x2, y2 = int(x + w), int(y + h)

    # Pilih emosi dominan
    top_items = topk_items(prob, k=topk)
    emo_main, p_main = top_items[0]

    color = EMO_COLORS.get(emo_main, (255, 255, 255))
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

    # Label atas dengan ID, emoji, dan skor
    label = f"ID {tid}  {EMO_EMOJI.get(emo_main, '')}  {emo_main} {p_main*100:.1f}%"
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 10, y1), color, -1)
    cv2.putText(frame, label, (x1 + 5, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2, cv2.LINE_AA)

    # Tampilkan Top-2 di bawah
    if len(top_items) > 1:
        emo2, p2 = top_items[1]
        sub = f"{emo2} {p2*100:.1f}%"
        cv2.putText(frame, sub, (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2, cv2.LINE_AA)

    # Mini bar chart di sisi kiri box
    if draw_bars:
        bar_w = 6
        bar_h = h // 2
        bar_x = x1 - 12
        cv2.rectangle(frame, (bar_x - 2, y1), (bar_x + bar_w + 2, y1 + bar_h), (50, 50, 50), 1)
        # Urutkan semua emosi agar konsisten
        keys = list(EMO_COLORS.keys())
        step = max(1, bar_h // len(keys))
        for i, k in enumerate(keys):
            p = float(prob.get(k, 0.0))
            length = int(bar_w * p)
            by = y1 + i * step
            cv2.rectangle(frame, (bar_x, by), (bar_x + length, by + step - 2), EMO_COLORS[k], -1)

# ----------------------------
# Main
# ----------------------------
def main():
    cap = cv2.VideoCapture(CFG["camera_index"])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CFG["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CFG["height"])

    if not cap.isOpened():
        print("Kamera tidak dapat dibuka.")
        return

    tracker = TrackManager(min_iou=CFG["min_iou_match"], alpha=CFG["ema_alpha"])

    t0 = time.time()
    frames = 0
    fps = 0.0

    print("Memulai realtime mood detection... Tekan 'q' untuk keluar.")
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frames += 1
        h, w = frame.shape[:2]
        dets = []
        t_now = time.time()

        # Analisis emosi tiap N frame
        if frames % CFG["frame_stride"] == 0:
            try:
                res = DeepFace.analyze(
                    frame,
                    actions=["emotion"],
                    detector_backend=CFG["detector_backend"],
                    enforce_detection=False,
                    align=CFG["align"],
                    silent=True
                )
                results = ensure_list(res)
                for r in results:
                    region = r.get("region", {})
                    x = int(region.get("x", 0))
                    y = int(region.get("y", 0))
                    w_box = int(region.get("w", 0))
                    h_box = int(region.get("h", 0))
                    # Validasi box
                    if w_box <= 0 or h_box <= 0:
                        continue

                    # Ambil probabilitas emosi
                    emo_raw = r.get("emotion", {})
                    # Normalisasi (kadang sudah ter-normalisasi, ini sekadar jaga-jaga)
                    emo_prob = softmax(emo_raw) if emo_raw else {}

                    # Clamp box ke frame
                    x = max(0, min(x, w - 1))
                    y = max(0, min(y, h - 1))
                    w_box = max(1, min(w_box, w - x))
                    h_box = max(1, min(h_box, h - y))

                    dets.append({
                        "box": [x, y, w_box, h_box],
                        "prob": emo_prob
                    })
            except Exception as e:
                # Hindari crash; lanjutkan loop
                # print(f"Warning analyze: {e}")
                dets = []

        # Update tracks dan dapatkan state terkini
        updates = tracker.match_and_update(dets, t_now)

        # Gambar hasil untuk semua track aktif
        for tid, st in tracker.tracks.items():
            draw_emotion_overlay(
                frame,
                tid=tid,
                box=st["box"],
                prob=st["prob"],
                topk=CFG["topk"],
                draw_bars=CFG["draw_bars"]
            )

        # Hitung FPS
        if frames % 10 == 0:
            t1 = time.time()
            fps = 10.0 / (t1 - t0)
            t0 = t1

        # Overlay FPS
        cv2.putText(frame, f"FPS {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)

        cv2.imshow("Mood Vision - Hikari", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()