import pygame
import threading
import random

state = {
    "mode": "eyes",
    "message": "",
    "data": None
}

lock = threading.Lock()


def set_message(text):
    with lock:
        state["mode"] = "message"
        state["message"] = text


def show_report(data):
    with lock:
        state["mode"] = "report"
        state["data"] = data


def show_eyes():
    with lock:
        state["mode"] = "eyes"


def gui_loop():

    pygame.init()

    # Fullscreen display (4K monitor)
    screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
    screen_w, screen_h = screen.get_size()

    # Internal rendering resolution (720p)
    render_w = 1280
    render_h = 720

    render_surface = pygame.Surface((render_w, render_h))

    font = pygame.font.SysFont("Arial", 40)

    clock = pygame.time.Clock()

    base_x = render_w // 2
    eye_offset = 150

    eye_shift = 0
    target_shift = 0

    blink_timer = 0
    blink = False

    running = True

    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        render_surface.fill((0,0,0))

        with lock:
            mode = state["mode"]

        # ---------------- EYES MODE ----------------

        if mode == "eyes":

            if random.randint(0,100) < 3:
                target_shift = random.randint(-40,40)

            eye_shift += (target_shift - eye_shift) * 0.1

            blink_timer += 1

            if blink_timer > 90:
                blink = True

            if blink:
                eye_h = 20
                if blink_timer > 95:
                    blink = False
                    blink_timer = 0
            else:
                eye_h = 80

            left_eye = (int(base_x-eye_offset+eye_shift), render_h//2)
            right_eye = (int(base_x+eye_offset+eye_shift), render_h//2)

            pygame.draw.ellipse(render_surface,(255,255,255),(left_eye[0],left_eye[1],140,eye_h))
            pygame.draw.ellipse(render_surface,(255,255,255),(right_eye[0],right_eye[1],140,eye_h))

        # ---------------- MESSAGE MODE ----------------

        elif mode == "message":

            with lock:
                text = state["message"]

            txt = font.render(text,True,(255,255,255))
            rect = txt.get_rect(center=(render_w//2,render_h//2))

            render_surface.blit(txt,rect)

        # ---------------- REPORT MODE ----------------

        elif mode == "report":

            with lock:
                data = state["data"]

            y = 150

            if data:
                for k,v in data.items():

                    txt = font.render(f"{k}: {v}",True,(255,255,255))
                    render_surface.blit(txt,(200,y))

                    y += 50

        # scale 720p → fullscreen 4k
        scaled = pygame.transform.smoothscale(render_surface,(screen_w,screen_h))
        screen.blit(scaled,(0,0))

        pygame.display.flip()

        clock.tick(12)

    pygame.quit()


def start_gui():

    thread = threading.Thread(target=gui_loop,daemon=True)
    thread.start()