import cv2
import mediapipe as mp
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time

# GUI Window
window = tk.Tk()
window.title("Jump Height Estimation")
window.geometry("400x400")
window.configure(bg='white')


video_source = None

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Functions
def select_video():
    global video_source
    video_source = filedialog.askopenfilename(title="Select Video File", filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
    cam_or_file_label.config(text="Video File Selected", fg='blue')

def select_camera():
    global video_source
    video_source = 0
    cam_or_file_label.config(text="Live Camera Selected", fg='blue')

def start_process():
    global person_height_cm, person_name
    name = name_entry.get()
    height = height_entry.get()

    if not name or not height:
        messagebox.showerror("Input Error", "Please enter both Name and Height.")
        return

    try:
        person_height_cm = float(height)
    except ValueError:
        messagebox.showerror("Input Error", "Height must be a number.")
        return

    person_name = name

    countdown_label.config(text="Starting in...")
    window.update()

    for i in range(3, 0, -1):
        countdown_label.config(text=f"{i}")
        window.update()
        time.sleep(1)

    countdown_label.config(text="GO!")
    window.update()

    # Start video processing in a new thread
    threading.Thread(target=process_video).start()

def process_video():
    global video_source, person_height_cm

    cap = cv2.VideoCapture(video_source)

    baseline_y = None
    max_jump_pixels = 0
    jumping = False
    jumps_cm = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            frame_height, frame_width, _ = frame.shape

            y_left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP].y
            y_right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y
            y_mid_hip = (y_left_hip + y_right_hip) / 2
            y_mid_hip_pixel = int(y_mid_hip * frame_height)

            y_head = landmarks[mp_pose.PoseLandmark.NOSE].y
            y_foot_left = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE].y
            y_foot_right = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE].y
            y_foot = max(y_foot_left, y_foot_right)
            height_in_pixels = abs((y_foot - y_head) * frame_height)

            if baseline_y is None:
                baseline_y = y_mid_hip_pixel
                baseline_height_pixels = height_in_pixels

            if height_in_pixels != 0:
                cm_per_pixel = person_height_cm / baseline_height_pixels
            else:
                cm_per_pixel = 1

            if y_mid_hip_pixel < baseline_y - 20:
                jumping = True
                jump_pixels = baseline_y - y_mid_hip_pixel
                max_jump_pixels = max(max_jump_pixels, jump_pixels)
            elif jumping and y_mid_hip_pixel >= baseline_y - 5:
                jump_cm = max_jump_pixels * cm_per_pixel
                jumps_cm.append(jump_cm)
                print(f"{person_name} Jump Height (cm): {jump_cm:.2f}")
                max_jump_pixels = 0
                jumping = False

            cv2.circle(frame, (int(landmarks[mp_pose.PoseLandmark.NOSE].x * frame_width), y_mid_hip_pixel), 10, (255, 0, 0), -1)

            if jumps_cm:
                max_jump = np.max(jumps_cm)
                min_jump = np.min(jumps_cm)
                avg_jump = np.mean(jumps_cm)
                total_jumps = len(jumps_cm)
                cv2.putText(frame, f"{person_name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                cv2.putText(frame, f"Jumps: {total_jumps}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                cv2.putText(frame, f"Max: {max_jump:.2f} cm", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, f"Min: {min_jump:.2f} cm", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(frame, f"Avg: {avg_jump:.2f} cm", (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        # Resize the frame smaller
        scale_percent = 50
        width = int(frame.shape[1] * scale_percent / 100)
        height = int(frame.shape[0] * scale_percent / 100)
        dim = (width, height)
        frame = cv2.resize(frame, dim, interpolation=cv2.INTER_AREA)

        cv2.imshow('Jump Height Estimation', frame)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# GUI Layout
header_label = tk.Label(window, text="Jump Height Estimation", font=('Arial', 18, 'bold'), fg='blue', bg='white')
header_label.pack(pady=10)

tk.Label(window, text="Enter Name:", font=('Arial', 12, 'bold'), fg='blue', bg='white').pack()
name_entry = tk.Entry(window, font=('Arial', 12))
name_entry.pack(pady=5)

tk.Label(window, text="Enter Height (cm):", font=('Arial', 12, 'bold'), fg='blue', bg='white').pack()
height_entry = tk.Entry(window, font=('Arial', 12))
height_entry.pack(pady=5)

cam_button = tk.Button(window, text="Use Live Camera", command=select_camera, font=('Arial', 12, 'bold'), bg='blue', fg='white')
cam_button.pack(pady=5)

video_button = tk.Button(window, text="Select Video File", command=select_video, font=('Arial', 12, 'bold'), bg='blue', fg='white')
video_button.pack(pady=5)

cam_or_file_label = tk.Label(window, text="", font=('Arial', 12), fg='blue', bg='white')
cam_or_file_label.pack(pady=5)

start_button = tk.Button(window, text="Start", command=start_process, font=('Arial', 14, 'bold'), bg='blue', fg='white')
start_button.pack(pady=10)

countdown_label = tk.Label(window, text="", font=('Arial', 20, 'bold'), fg='blue', bg='white')
countdown_label.pack(pady=10)

window.mainloop()