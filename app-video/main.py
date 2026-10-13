import cv2
import time
from collections import deque
from datetime import datetime
from pathlib import Path


BUFFER_SECONDS = 30
REPLAY_SECONDS = 10
JPEG_QUALITY = 80

CAMERA_MODES = [
    (1280, 720, 30),
    (640, 480, 30),
    (640, 480, 25),
    (640, 480, 20),
    (320, 240, 30),
]


def open_camera():
    for camera_index in range(4):
        camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not camera.isOpened():
            camera.release()
            camera = cv2.VideoCapture(camera_index)
        if not camera.isOpened():
            camera.release()
            continue

        for width, height, fps in CAMERA_MODES:
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            camera.set(cv2.CAP_PROP_FPS, fps)

            valid = True
            for _ in range(5):
                ok, frame = camera.read()
                if not ok or frame is None:
                    valid = False
                    break
            if valid:
                actual_height, actual_width = frame.shape[:2]
                actual_fps = camera.get(cv2.CAP_PROP_FPS)
                if actual_fps <= 0:
                    actual_fps = fps
                print(
                    f"Webcam {camera_index} pronta: {actual_width}x{actual_height}, "
                    f"aprox. {actual_fps:g} FPS"
                )
                return camera, actual_width, actual_height, actual_fps

        camera.release()
    raise RuntimeError("A webcam abriu, mas não entregou quadros nos modos testados.")


def save_replay(frames, width, height):
    if len(frames) < 2:
        raise RuntimeError("Ainda não há quadros suficientes para criar o replay.")

    elapsed = frames[-1][0] - frames[0][0]
    if elapsed <= 0:
        raise RuntimeError("Não foi possível calcular a duração do replay.")

    fps = (len(frames) - 1) / elapsed
    now = datetime.now()
    output_path = Path.cwd() / f"replay_{now:%Y-%m-%d_%H-%M-%S}.mp4"
    writer = cv2.VideoWriter(
        str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )
    if not writer.isOpened():
        raise RuntimeError("Não foi possível criar MP4 com o codec mp4v do OpenCV.")

    try:
        for _, jpeg in frames:
            frame = cv2.imdecode(jpeg, cv2.IMREAD_COLOR)
            if frame is not None:
                writer.write(frame)
    finally:
        writer.release()
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("O MP4 não foi gravado corretamente.")
    return output_path, elapsed, fps


def main():
    camera, width, height, fps = open_camera()
    buffer = deque()
    window_name = "Replay de webcam | R: salvar replay | Q: sair"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    last_status = "Aguardando 10 segundos para habilitar o replay..."
    last_status_time = time.monotonic()

    try:
        while True:
            ok, frame = camera.read()
            if not ok or frame is None:
                print("Falha ao ler imagem da webcam.")
                break

            captured_at = time.monotonic()
            encoded_ok, jpeg = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
            )
            if encoded_ok:
                buffer.append((captured_at, jpeg))

            cutoff = captured_at - BUFFER_SECONDS
            while buffer and buffer[0][0] < cutoff:
                buffer.popleft()

            visible_status = last_status if captured_at - last_status_time < 4 else ""
            cv2.putText(
                frame,
                f"Buffer: {min(BUFFER_SECONDS, captured_at-buffer[0][0]) if buffer else 0:.1f}s  |  R: replay  |  Q: sair",
                (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2,
            )
            if visible_status:
                cv2.putText(
                    frame, visible_status, (12, 58), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, (0, 255, 255), 2,
                )
            cv2.imshow(window_name, frame)

            key = cv2.waitKey(1) & 0xFF
            key = chr(key).lower() if 0 <= key < 128 else ""
            if key == "q":
                break
            if key == "r":
                replay_cutoff = captured_at - REPLAY_SECONDS
                replay_frames = [item for item in buffer if item[0] >= replay_cutoff]
                duration = replay_frames[-1][0] - replay_frames[0][0] if len(replay_frames) > 1 else 0
                if duration < REPLAY_SECONDS * 0.9:
                    last_status = "Buffer ainda sem 10 segundos. Tente novamente em instantes."
                else:
                    try:
                        path, elapsed, replay_fps = save_replay(replay_frames, width, height)
                        last_status = f"Replay salvo: {path.name}"
                        print(
                            f"Replay salvo em: {path} "
                            f"({len(replay_frames)} quadros, {elapsed:.1f} s, "
                            f"{replay_fps:.1f} FPS)"
                        )
                    except RuntimeError as error:
                        last_status = str(error)
                        print(error)
                last_status_time = time.monotonic()
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(error)
