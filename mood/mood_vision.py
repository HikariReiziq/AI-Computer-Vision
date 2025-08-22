import sys
import subprocess

# ----------------------------
# Auto-install dependencies
# ----------------------------
REQUIRED = [
    "opencv-python",
    "deepface",
    "mediapipe",
    "numpy",
    "tf-keras"  # khusus untuk TensorFlow >= 2.16 yang dipakai DeepFace/RetinaFace
]

def install_missing():
    import importlib
    for pkg in REQUIRED:
        try:
            importlib.import_module(pkg.split("==")[0].replace("-", "_"))
        except ImportError:
            print(f"[Installer] Menginstal: {pkg} ...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

install_missing()

# ----------------------------
# Lanjut ke mood detector
# ----------------------------
import cv2
import numpy as np
import time
from collections import defaultdict
from typing import List, Tuple, Dict
from deepface import DeepFace

# --- Konfigurasi ---
CFG = {
    "camera_index": 0,
    "width": 1280,
    "height": 720,
    "frame_stride": 2,
    "ema_alpha": 0.7,
    "min_iou_match": 0.3,
    "detector_backend": "mediapipe",
    "align": True,
    "draw_bars": True,
    "topk": 2
}

EMO_COLORS = {
    "happy": (40, 200, 40),
    "sad": (200, 120, 40),
    "angry": (50, 50, 230),
    "surprise": (40, 180, 240),
    "fear": (180, 100, 200),
    "disgust": (0, 180, 120),
    "neutral": (200, 200, 200)
}

EMO_EMOJI = {
    "happy": "😄", "sad": "😢", "angry": "😠",
    "surprise": "😮", "fear": "😨", "disgust": "🤢",
    "neutral": "😐"
}

# --- Utilitas ---
def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])
    inter = max(0, xB - xA) * max(0, yB - yA)
    denom = (boxA[2] * boxA[3]) + (boxB[2] * boxB[3]) - inter + 1e-6
    return inter / denom

def ensure_list(r):
    return r if isinstance(r, list) else [r]

def softmax(d):
    vals = np.array(list(d.values()), dtype=np.float32)
    e = np.exp(vals - vals.max())
    p = (e / e.sum()).tolist()
    return {k: v for k, v in zip(d.keys(), p)}

def topk_items(prob, k=2):
    return sorted(prob.items(), key=lambda x: x[1], reverse=True)[:k]

# --- Tracking ---
class TrackManager:
    def __init__(self, min_iou=0.3, alpha=0.7):
        self.next_id = 1
        self.tracks = {}
        self.min_iou = min_iou
        self.alpha = alpha

    def match_and_update(self, dets, t_now):
        assigned = set()
        updates = {}
        for det in dets:
            best_iou, best_id = 0, None
            for tid, tr in self.tracks.items():
                i = iou(det["box"], tr["box"])
                if i > best_iou and i >= self.min_iou and tid not in assigned:
                    best_iou, best_id = i, tid
            if best_id is None:
                tid = self.next_id; self.next_id += 1
                self.tracks[tid] = {"box": det["box"], "prob": det["prob"], "last_t": t_now}
                assigned.add(tid); updates[tid] = self.tracks[tid]
            else:
                old = self.tracks[best_id]["prob"]
                new_prob = {k: self.alpha*old.get(k,0)+(1-self.alpha)*det["prob"].get(k,0)
                            for k in set(old)|set(det["prob"])}
                self.tracks[best_id].update({"box": det["box"], "prob": new_prob, "last_t": t_now})
                assigned.add(best_id); updates[best_id] = self.tracks[best_id]
        for tid in [tid for tid,tr in self.tracks.items() if t_now - tr["last_t"] > 2]:
            del self.tracks[tid]
        return updates

# --- Visual ---
def draw_overlay(frame, tid, box, prob, topk=2, draw_bars=True):
    x, y, w, h = box; x1, y1 = int(x), int(y); x2, y2 = int(x+w), int(y+h)
    emo_main, p_main = topk_items(prob, k=topk)[0]
    color = EMO_COLORS.get(emo_main, (255,255,255))
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    label = f"ID {tid} {EMO_EMOJI.get(emo_main,'')} {emo_main} {p_main*100:.1f}%"
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    cv2.rectangle(frame, (x1, y1-th-10), (x1+tw+10, y1), color, -1)
    cv2.putText(frame, label, (x1+5, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,0), 2)
    if draw_bars:
        bar_x = x1 - 12; keys = list(EMO_COLORS.keys()); step = max(1, h//(2*len(keys)))
        for i, k in enumerate(keys):
            p = float(prob.get(k, 0.0)); length = int(6 * p)
            by = y1 + i * step
            cv2.rectangle(frame, (bar_x, by), (bar_x + length, by + step - 1), EMO_COLORS[k], -1)

# --- Main ---
def main():
    cap = cv2.VideoCapture(CFG["camera_index"])
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CFG["width"])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CFG["height"])
    if not cap.isOpened():
        print("Kamera tidak terbuka."); return
    tracker = TrackManager(min_iou=CFG["min_iou_match"], alpha=CFG["ema_alpha"])
    t0 = time.time(); frames = 0; fps = 0
    while True:
        ok, frame = cap.read()
        if not ok: break
        frames += 1; t_now = time.time(); dets = []
        if frames % CFG["frame_stride"] == 0:
            try:
                res = DeepFace.analyze(frame, actions=["emotion"], detector_backend=CFG["detector_backend"],
                                       enforce_detection=False, align=CFG["align"], silent=True)
                for r in ensure_list(res):
                    region = r.get("region", {})
                    x, y, w_box, h_box = map(int, [region.get("x",0), region.get("y",0), region.get("w",0), region.get("h",0)])
                    if w_box>0 and h_box>0:
                        prob = softmax(r.get("emotion", {}))
                        dets.append({"box":[x,y,w_box,h_box], "prob":prob})
            except Exception as e:
                pass
        tracker.match_and_update(dets, t_now)
        for tid, st in tracker.tracks.items():
            draw_overlay(frame, tid, st["box"], st["prob"], topk=CFG["topk"], draw_bars=CFG["draw_bars"])
        if frames % 10 == 0:
            t1 = time.time(); fps = 10/(t1-t0); t0 = t1
        cv2.putText(frame, f"FPS {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,255,255), 2)
        cv2.imshow("Mood Vision Auto", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release(); cv2.destroyAllWindows