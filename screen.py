import pygame
import threading
import random
from enum import Enum

# ---------- EMOTIONS ----------

class Emotion(Enum):
    NORMAL = 0
    CURIOUS = 1
    EXCITED = 2
    SLEEPY = 3
    BLINK = 4
    HAPPY = 5
    SAD = 6
    ANGRY = 7


# ---------- STATE ----------

state = {
    "screen": "eyes",
    "emotion": Emotion.NORMAL,
    "message": "",
    "data": None
}

lock = threading.Lock()


# ---------- API ----------

def set_emotion(e):
    with lock:
        state["emotion"] = e
        state["screen"] = "eyes"


def set_message(text):
    with lock:
        state["screen"] = "message"
        state["message"] = text


def show_report(data):
    with lock:
        state["screen"] = "report"
        state["data"] = data


def show_eyes():
    with lock:
        state["screen"] = "eyes"


# ---------- DRAW ----------

def draw_eye(surface, x, y, size):
    pygame.draw.rect(
        surface,
        (255,255,255),
        (x,y,size,size),
        border_radius=int(size*0.25)
    )


# ---------- GUI LOOP ----------

def gui_loop():

    pygame.init()

    screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
    width, height = screen.get_size()

    font = pygame.font.SysFont("Arial", 40)

    clock = pygame.time.Clock()

    # ---- eye geometry ----

    eye_size = int(height * 0.28)
    gap = int(width * 0.08)

    center_x = width // 2
    center_y = height // 2

    # ---- eye movement ----

    offset_x = 0
    offset_y = 0

    next_move_time = 0

    scan_pattern = [
        (0,0),
        (-width//4,0),
        (width//4,0),
        (0,0)
    ]

    scan_index = 0

    # ---- blinking ----

    last_blink = 0
    blink_time = 120
    blinking = False
    blink_delay = random.randint(4000,7000)

    # ---- text cache ----

    text_cache = None
    last_text = ""

    running = True

    while running:

        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill((0,0,0))

        with lock:
            screen_mode = state["screen"]
            emotion = state["emotion"]
            message = state["message"]
            data = state["data"]

        # ================= EYES ================= #

        if screen_mode == "eyes":

            # ----- eye movement -----

            if now > next_move_time:

                if random.random() < 0.4:
                    offset_x, offset_y = scan_pattern[scan_index]
                    scan_index = (scan_index + 1) % len(scan_pattern)
                else:
                    offset_x = random.randint(-width//4, width//4)
                    offset_y = random.randint(-height//6, height//6)

                next_move_time = now + random.randint(600,5000)

            # ----- blinking -----

            if not blinking and now - last_blink > blink_delay:
                blinking = True
                last_blink = now

            if blinking:
                draw_emotion = Emotion.BLINK

                if now - last_blink > blink_time:
                    blinking = False
                    last_blink = now
                    blink_delay = random.randint(4000,7000)
                    draw_emotion = emotion
            else:
                draw_emotion = emotion

            # ----- eye positions -----

            left_x = center_x - gap//2 - eye_size + offset_x
            right_x = center_x + gap//2 + offset_x
            y = center_y - eye_size//2 + offset_y

            # ----- emotions -----

            if draw_emotion == Emotion.NORMAL:

                draw_eye(screen,left_x,y,eye_size)
                draw_eye(screen,right_x,y,eye_size)

            elif draw_emotion == Emotion.CURIOUS:

                draw_eye(screen,left_x,y,eye_size)
                draw_eye(screen,right_x,y+25,eye_size)

            elif draw_emotion == Emotion.EXCITED:

                big = int(eye_size * 1.2)

                draw_eye(
                    screen,
                    center_x - gap//2 - big + offset_x,
                    center_y - big//2 + offset_y,
                    big
                )

                draw_eye(
                    screen,
                    center_x + gap//2 + offset_x,
                    center_y - big//2 + offset_y,
                    big
                )

            elif draw_emotion == Emotion.SLEEPY:

                sleepy_h = int(eye_size * 0.35)

                pygame.draw.rect(
                    screen,(255,255,255),
                    (left_x,y+eye_size//3,eye_size,sleepy_h),
                    border_radius=20
                )

                pygame.draw.rect(
                    screen,(255,255,255),
                    (right_x,y+eye_size//3,eye_size,sleepy_h),
                    border_radius=20
                )

            elif draw_emotion == Emotion.BLINK:

                blink_h = int(eye_size * 0.15)

                pygame.draw.rect(
                    screen,(255,255,255),
                    (left_x,y+eye_size//2,eye_size,blink_h),
                    border_radius=20
                )

                pygame.draw.rect(
                    screen,(255,255,255),
                    (right_x,y+eye_size//2,eye_size,blink_h),
                    border_radius=20
                )

            elif draw_emotion == Emotion.HAPPY:

                happy_h = int(eye_size * 0.55)

                pygame.draw.rect(
                    screen,(255,255,255),
                    (left_x, y + eye_size*0.25, eye_size, happy_h),
                    border_radius=30
                )

                pygame.draw.rect(
                    screen,(255,255,255),
                    (right_x, y + eye_size*0.25, eye_size, happy_h),
                    border_radius=30
                )

            elif draw_emotion == Emotion.SAD:

                sad_h = int(eye_size * 0.7)

                pygame.draw.rect(
                    screen,(255,255,255),
                    (left_x, y + 40, eye_size, sad_h),
                    border_radius=40
                )

                pygame.draw.rect(
                    screen,(255,255,255),
                    (right_x, y + 40, eye_size, sad_h),
                    border_radius=40
                )

            elif draw_emotion == Emotion.ANGRY:

                tilt = 30

                pygame.draw.polygon(
                    screen,(255,255,255),
                    [
                        (left_x, y+tilt),
                        (left_x+eye_size, y),
                        (left_x+eye_size, y+eye_size),
                        (left_x, y+eye_size)
                    ]
                )

                pygame.draw.polygon(
                    screen,(255,255,255),
                    [
                        (right_x, y),
                        (right_x+eye_size, y+tilt),
                        (right_x+eye_size, y+eye_size),
                        (right_x, y+eye_size)
                    ]
                )


        # ================= MESSAGE ================= #

        elif screen_mode == "message":

            if message != last_text:
                text_cache = font.render(message,True,(255,255,255))
                last_text = message

            rect = text_cache.get_rect(center=(width//2,height//2))
            screen.blit(text_cache,rect)


        # ================= REPORT ================= #

        elif screen_mode == "report":

            y_pos = 150

            if data:

                for k,v in data.items():

                    txt = font.render(f"{k}: {v}",True,(255,255,255))
                    screen.blit(txt,(200,y_pos))

                    y_pos += 60

        pygame.display.flip()

        clock.tick(5)   # low CPU


    pygame.quit()


# ---------- START ----------

def start_gui():
    
    thread = threading.Thread(target=gui_loop,daemon=True)
    thread.start()