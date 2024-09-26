from flask import Flask, Response
from PIL import Image
import pyautogui
import imageio
import io
import time
import mss
import mss.tools
import numpy as np

# Run this server and then open https://dosgames.club/shooter/doom.html to control DOOM
# You may need to adjust the coordinates below to match the size of the DOOM window on your
# computer

app = Flask(__name__)

def do_screenshot(use_pyautogui=False):
    divisor = 2

    # Hardcoded coordinates of the DOOM window on nolen's laptop
    left = 742 / divisor
    top = 734 / divisor
    width = 1540 / divisor
    height = 960 / divisor
    right = left + width
    bottom = top + height

    if use_pyautogui:
        screenshot = pyautogui.screenshot()
        cropped_image = screenshot.crop((left, top, right, bottom))
        cropped_image = cropped_image.resize((cropped_image.width // 2, cropped_image.height // 2))
        return cropped_image
    else:
        with mss.mss() as sct:
            region = { "top": top, "left": left, "width": width, "height": height }
            sct_img = sct.grab(region)
            img = Image.frombytes('RGB', (sct_img.width, sct_img.height), sct_img.rgb)
            return img

# Swap this in for `send_command_while_recording` if you want to return static images
def __image_send_command_while_recording(keys, delay=0.015, num_frames=3):
    for key in keys:
        pyautogui.keyDown(key)

    # We need this for things like forward/back, since otherwise the key is only registered for like
    # a millisecond and you barely move
    time.sleep(0.10)
    frame = do_screenshot(use_pyautogui=True)

    for key in keys:
        pyautogui.keyUp(key)

    img_io = io.BytesIO()
    frame.save(img_io, format='PNG')
    img_io.seek(0)

    response = Response(img_io.getvalue(), mimetype='image/png')
    response.headers.set('Content-Disposition', 'inline', filename='screenshot.png')

    return response

# Swap this in for `send_command_while_recording` if you want to return gifs
def __send_gif_while_recording(keys, delay=0.015, num_frames=3):
    start_time = time.time()
    frames = [x for x in OLD_SCREENSHOT if x is not None]
    if not frames:
        frames.append(do_screenshot(use_pyautogui=True))

    for key in keys:
        pyautogui.keyDown(key)

    for _ in range(num_frames):
        s = do_screenshot(use_pyautogui=True)
        # We need this for things like forward/back, since otherwise the key is only registered for like
        # a millisecond and you barely move
        time.sleep(delay)
        frames.append(s)

    for key in keys:
        pyautogui.keyUp(key)

    end_time = time.time()
    total_time = end_time - start_time
    duration = max(0.1, total_time / len(frames))
    fps = 1 / duration

    img_io = io.BytesIO()
    with imageio.get_writer(img_io, format='GIF', mode='I', duration=duration) as writer:
        for frame in frames:
            # Convert PIL image to numpy array by saving it to a BytesIO object first
            byte_io = io.BytesIO()
            frame.save(byte_io, format='PNG')
            byte_io.seek(0)
            writer.append_data(imageio.imread(byte_io))

    img_io.seek(0)
    response = Response(img_io.getvalue(), mimetype='image/gif')
    response.headers.set('Content-Disposition', 'inline', filename='screenshot.gif')
    return response

# Use the last image of our last screenshot as the first image of our new one
# (for continuity)
OLD_SCREENSHOT = [None]
def send_command_while_recording(keys, delay=0.015, num_frames=6):
    start_time = time.time()
    frames = [x for x in OLD_SCREENSHOT if x is not None]
    if not frames:
        frames.append(do_screenshot())

    for key in keys:
        pyautogui.keyDown(key)

    for _ in range(num_frames):
        s = do_screenshot()
        # We need this for things like forward/back, since otherwise the key is only registered for like
        # a millisecond and you barely move
        time.sleep(delay)
        frames.append(s)

    for key in keys:
        pyautogui.keyUp(key)

    frames.append(do_screenshot())
    OLD_SCREENSHOT[0] = frames[-1]

    end_time = time.time()
    total_time = end_time - start_time
    duration = total_time / len(frames)
    fps = 1/ duration

    video_io = io.BytesIO()
    with imageio.get_writer(video_io, format='mp4', fps=fps) as writer:
        for i, frame in enumerate(frames):
            writer.append_data(np.array(frame))

        for _ in range(50):
            writer.append_data(np.array(frames[-1]))

    video_io.seek(0)
    response = Response(video_io.getvalue(), mimetype='video/mp4')
    response.headers.set("Content-Type", "video/mp4")
    response.headers.set('Content-Disposition', 'attachment', filename='screenshot.mp4')
    return response

@app.route('/forward', methods=['GET'])
def press_up():
    return send_command_while_recording(["up"])

@app.route('/backward', methods=['GET'])
def press_down():
    return send_command_while_recording(["down"])

@app.route('/fire', methods=['GET'])
def fire():
    return send_command_while_recording(["ctrl"])

@app.route('/left', methods=['GET'])
def press_left():
    return send_command_while_recording(["left"])

@app.route('/right', methods=['GET'])
def press_right():
    return send_command_while_recording(["right"])

@app.route('/strafeLeft', methods=['GET'])
def strafe_left():
    return send_command_while_recording(["alt", "left"])

@app.route('/strafeRight', methods=['GET'])
def strafe_right():
    return send_command_while_recording(["alt", "right"])

@app.route('/use', methods=['GET'])
def use():
    return send_command_while_recording(["space", "enter"])

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=8000)
    finally:
        # Release the video stream when the webserver is stopped
        cap.release()
