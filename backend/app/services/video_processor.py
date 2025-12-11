# backend/app/services/video_processor.py
import cv2
import numpy as np
import tempfile
import os
from pathlib import Path
from typing import Dict, Tuple

import mediapipe as mp

mp_pose = mp.solutions.pose
mp_face_mesh = mp.solutions.face_mesh

# helper: compute angle between three points (in degrees)
def _angle_between(a, b, c):
    # angle at b formed by points a-b-c
    ba = np.array(a) - np.array(b)
    bc = np.array(c) - np.array(b)
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-9)
    cosine = np.clip(cosine, -1.0, 1.0)
    angle = np.degrees(np.arccos(cosine))
    return float(angle)

def _percentage_in_range(values, low, high):
    if len(values) == 0:
        return 0.0
    arr = np.array(values)
    return float(((arr >= low) & (arr <= high)).sum() / arr.size)

async def analyze_video_file(upload_file) -> Dict:
    """
    Save uploaded video -> sample frames -> run MediaPipe Pose + FaceMesh.
    Returns posture/gaze/movement stats and scores (0-100).
    """
    suffix = Path(upload_file.filename).suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        contents = await upload_file.read()
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            raise RuntimeError("Cannot open video file for processing.")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = frame_count / fps if fps > 0 else 0.0

        # sample every Nth frame to speed up
        sample_rate = max(1, int(fps * 0.5))  # roughly 1 sample every 2 seconds
        frames_analyzed = 0

        shoulder_tilt_list = []
        gaze_contact_list = []   # 1 if eyes facing camera-like, else 0
        movement_magnitudes = []

        prev_landmarks = None
        prev_nose = None

        pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)
        face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5)

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1

            if frame_idx % sample_rate != 0:
                continue

            frames_analyzed += 1
            # convert BGR -> RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Pose
            pose_res = pose.process(rgb)
            if pose_res.pose_landmarks:
                lm = pose_res.pose_landmarks.landmark
                # shoulder points: left (11), right (12) - mp indices
                left_sh = lm[11]
                right_sh = lm[12]
                # convert to image coords
                h, w, _ = frame.shape
                left_sh_pt = (left_sh.x * w, left_sh.y * h)
                right_sh_pt = (right_sh.x * w, right_sh.y * h)
                # compute tilt angle of shoulders relative to horizontal
                dx = right_sh_pt[0] - left_sh_pt[0]
                dy = right_sh_pt[1] - left_sh_pt[1]
                tilt_rad = np.arctan2(dy, dx)
                tilt_deg = np.degrees(tilt_rad)
                shoulder_tilt_list.append(abs(tilt_deg))
                # movement magnitude (nose movement)
                nose = lm[0]
                nose_pt = (nose.x * w, nose.y * h)
                if prev_nose is not None:
                    movement = np.linalg.norm(np.array(nose_pt) - np.array(prev_nose))
                    movement_magnitudes.append(movement)
                prev_nose = nose_pt
            else:
                # no pose landmarks detected, add mild penalty by assuming larger tilt
                shoulder_tilt_list.append(30.0)

            # Face / gaze: use nose + inner eye landmarks to approximate facing direction
            face_res = face_mesh.process(rgb)
            if face_res.multi_face_landmarks and len(face_res.multi_face_landmarks) > 0:
                fm = face_res.multi_face_landmarks[0].landmark
                # Using landmarks: nose tip ~1, left eye inner ~33, right eye inner ~263 (indices may vary; this is approximate)
                # For robustness, try multiple indices and fallback
                try:
                    nose_lm = fm[1]
                    left_eye = fm[33]
                    right_eye = fm[263]
                    # vector from nose to midpoint of eyes
                    eye_mid = ((left_eye.x + right_eye.x) / 2.0, (left_eye.y + right_eye.y) / 2.0)
                    nose_pt = (nose_lm.x, nose_lm.y)
                    # simple heuristic: if nose is roughly centered between eyes horizontally and not strongly tilted, likely facing camera
                    horiz_offset = abs(nose_pt[0] - eye_mid[0])
                    vert_offset = abs(nose_pt[1] - eye_mid[1])
                    # thresholds tuned empirically
                    if horiz_offset < 0.03 and vert_offset < 0.05:
                        gaze_contact_list.append(1)
                    else:
                        gaze_contact_list.append(0)
                except Exception:
                    gaze_contact_list.append(0)
            else:
                gaze_contact_list.append(0)

        # cleanup mediapipe
        pose.close()
        face_mesh.close()
        cap.release()

        # compute stats
        frames_analyzed = max(1, frames_analyzed)
        avg_shoulder_tilt = float(np.mean(shoulder_tilt_list)) if shoulder_tilt_list else 30.0
        # percent eye contact
        percent_eye_contact = float(np.sum(gaze_contact_list) / len(gaze_contact_list)) if gaze_contact_list else 0.0
        # movement score: high movement magnitude -> lower score
        avg_movement = float(np.mean(movement_magnitudes)) if movement_magnitudes else 0.0

        # Score heuristics (0-100)
        # Posture: shoulder tilt near 0 is ideal; penalize larger tilt
        posture_score = int(max(0, min(100, 100 - (avg_shoulder_tilt * 1.5))))  # ~0 deg ->100, 30deg->55
        # Gaze: percent eye contact scaled to 0-100
        gaze_score = int(round(min(100, percent_eye_contact * 100)))
        # Movement: prefer small movement; large movements lower score
        movement_score = int(max(0, min(100, 100 - avg_movement * 50)))

        video_stats = {
            "duration_seconds": round(duration, 2),
            "frames_analyzed": int(frames_analyzed),
            "avg_shoulder_tilt_deg": round(avg_shoulder_tilt, 2),
            "percent_eye_contact": round(percent_eye_contact, 3),
        }

        video_scores = {
            "posture_score": int(posture_score),
            "gaze_score": int(gaze_score),
            "movement_score": int(movement_score),
        }

        return {
            "scores": video_scores,
            "stats": video_stats,
        }

    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
