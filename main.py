import pygame
import sys
import random
import time
import os
import json
import asyncio

# Get the base path for assets (important when running as a .exe)
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

pygame.init()
pygame.mixer.init()
try:
    pygame.mixer.music.load(os.path.join(base_path, 'assets', "background_music.mp3"))
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)  # loop forever
except pygame.error as e:
    print(f"Error loading music: {e}")
    print("Make sure the background_music.mp3 file is in the assets folder.")



jump_sound = pygame.mixer.Sound(os.path.join(base_path, 'assets', "player_jump.wav"))
jump_sound.set_volume(0.5)
bonus_sound = pygame.mixer.Sound(os.path.join(base_path, 'assets', "bonus_earned.wav"))
bonus_sound.set_volume(0.5)
impact_sound = pygame.mixer.Sound(os.path.join(base_path, 'assets', "impact_hit.wav"))
impact_sound.set_volume(0.7)


WIDTH, HEIGHT = 400, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Elevator Jump")

# Images
background_img = pygame.image.load(os.path.join(base_path, 'assets', "elevator_jump_background.png"))
background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
background_img.set_colorkey((255, 255, 255))  

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
RED = (200, 50, 50)
GREEN = (50, 200, 50)
GOLD = (255, 215, 0)
LIGHT_YELLOW = (255, 255, 150)
DARK_GRAY = (50, 50, 50)

clock = pygame.time.Clock()
FPS = 60

font = pygame.font.SysFont(None, 36)

SAVE_FILE = "highscore.json"
highscore = 1
if os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "r") as f:
        try:
            highscore = json.load(f)["highscore"]
        except:
            highscore = 1

def save_highscore(score):
    with open(SAVE_FILE, "w") as f:
        json.dump({"highscore": score}, f)

def draw_text(text, color, y_offset=0, center=True, pos=(0,0), size=36):
    fnt = pygame.font.SysFont(None, size)
    label = fnt.render(text, True, color)
    if center:
        rect = label.get_rect(center=(WIDTH//2, HEIGHT//2 + y_offset))
    else:
        rect = label.get_rect(topleft=pos)
    screen.blit(label, rect)

def draw_ground():
    pygame.draw.rect(screen, GRAY, (0, HEIGHT - 50, WIDTH, 10))

def wait_for_space():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                return
        draw_text("Press SPACE to continue", BLACK, 80)
        pygame.display.flip()
        clock.tick(FPS)

def get_background(level):
    if level % 15 < 5:
        return WHITE
    elif level % 15 < 10:
        return DARK_GRAY
    else:
        return (30, 30, 60)
    
def show_welcome_modal():
    screen.blit(background_img, (0, 0))
    modal_rect = pygame.Rect(WIDTH//2 - 175, HEIGHT//2 - 200, 350, 400)
    pygame.draw.rect(screen, (240, 240, 240), modal_rect)
    pygame.draw.rect(screen, DARK_GRAY, modal_rect, 4)

    draw_text("Elevator Jump", BLACK, center=True, y_offset=-100, size=44)
    draw_text("Press SPACE to jump", BLACK, center=True, y_offset=-40)
    draw_text("You can only jump once!", BLACK, center=True, y_offset=0)
    draw_text("Jump just before impact...", BLACK, center=True, y_offset=30)

    pygame.display.flip()
    wait_for_space()


def game_loop():
    global highscore
    combo_counter = 0
    level = 1

    music_muted = False

    while True:
        elevator_width = random.randint(180, 220)
        elevator_height = 200
        elevator_x = (WIDTH - elevator_width) // 2
        elevator_y = -random.randint(300, 800)
        player_size = 40
        player_x = elevator_x + (elevator_width - player_size) // 2
        ground_y = HEIGHT - 50

        player_y = elevator_y + elevator_height - player_size - 10
        player_velocity = 0
        gravity = 0.6
        jump_strength = -6

        trail_positions = []

        fall_speed = 5 + level * 1.2
        jumped = False
        jump_time = None
        survived = False
        perfect_jump = False
        double_jump_used = False
        double_jump_available = level % 7 == 0
        slow_motion = level % 5 == 0
        safe_pad = level % 9 == 0

        if slow_motion:
            fall_speed *= 0.6

        is_jumping = False
        squash_time = 0
        jump_start_time = 0
        spark_frames = 0
        camera_shake = 0

        if random.random() < 0.3:
            elevator_y += 20
            screen.blit(background_img, (0, 0))
            draw_text("...", BLACK, y_offset=-200)
            pygame.display.flip()
            pygame.time.wait(200)

        falling = True

        while falling:
            if camera_shake > 0:
                offset_x = random.randint(-5, 5)
                offset_y = random.randint(-5, 5)
                camera_shake -= 1
            else:
                offset_x = offset_y = 0

            screen.blit(background_img, (0, 0))

            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if not jumped:
                            jumped = True
                            jump_time = time.time()
                            is_jumping = True
                            player_velocity = jump_strength
                            jump_sound.play()
                        elif double_jump_available and not double_jump_used:
                            jump_time = time.time()
                            is_jumping = True
                            player_velocity = jump_strength
                            double_jump_used = True
                            jump_sound.play()
                    elif event.key == pygame.K_m:
                        music_muted = not music_muted
                        if music_muted:
                            pygame.mixer.music.pause()
                        else:
                            pygame.mixer.music.unpause()

            elevator_y += fall_speed
            if not jumped:
                player_y = elevator_y + elevator_height - player_size - 10
            else:
                player_velocity += gravity
                player_y += player_velocity

            if jumped and player_y <= elevator_y:
                survived = False
                falling = False

            if player_y > elevator_y + elevator_height - player_size - 10:
                player_y = elevator_y + elevator_height - player_size - 10
                player_velocity = 0
                is_jumping = False

            trail_positions.append((player_x, player_y))
            if len(trail_positions) > 5:
                trail_positions.pop(0)

            draw_ground()

            # Draw elevator
            elevator_rect = pygame.Rect(elevator_x + offset_x, elevator_y + offset_y, elevator_width, elevator_height)
            pygame.draw.rect(screen, (200, 200, 200), elevator_rect)  # elevator fill
            pygame.draw.rect(screen, DARK_GRAY, elevator_rect, 4)     # elevator border

            # Draw elevator panel
            panel_w, panel_h = 20, 60
            panel_x = elevator_rect.right - 30
            panel_y = elevator_rect.top + 30
            pygame.draw.rect(screen, (100, 100, 100), (panel_x, panel_y, panel_w, panel_h))
            for i in range(3):
                pygame.draw.circle(screen, (180, 180, 180), (panel_x + 10, panel_y + 10 + i*20), 3)
            if safe_pad:
                pygame.draw.rect(screen, LIGHT_YELLOW, (elevator_x + 30, ground_y - 10, elevator_width - 60, 10))

            for i, pos in enumerate(trail_positions[:-1]):
                trail = pygame.Surface((player_size, player_size), pygame.SRCALPHA)
                alpha = 50 - i * 10
                trail.fill((255, 100, 100, alpha))
                screen.blit(trail, (pos[0] + offset_x, pos[1] + offset_y))

            pygame.draw.rect(screen, RED, (player_x + offset_x, player_y + offset_y, player_size, player_size))
            #pygame.draw.circle(screen, RED, (player_x + offset_x + player_size // 2, player_y + offset_y + player_size // 2), player_size // 2)

            draw_text(f"Level: {level}", BLACK, center=False, pos=(10, 10))
            draw_text(f"Best: {highscore}", BLACK, center=False, pos=(10, 40))
            if music_muted:
                draw_text("Music Off [M]", BLACK, center=False, pos=(240, 10))
            else:
                draw_text("Music On [M]", BLACK, center=False, pos=(240, 10))

            if slow_motion:
                draw_text("Slow Motion!", BLACK, center=False, pos=(10, 70))
            if double_jump_available:
                draw_text("Double Jump Ready!", BLACK, center=False, pos=(10, 100))
            if safe_pad:
                draw_text("Safe Pad Active", BLACK, center=False, pos=(10, 130))

            if elevator_y + elevator_height >= ground_y:
                falling = False
                impact_time = time.time()
                if jumped and 0 < impact_time - jump_time < 0.3:
                    survived = True
                    perfect_jump = (impact_time - jump_time) < 0.1
                    if perfect_jump:
                        combo_counter += 1
                        bonus_sound.play()
                        bonus = 2 + (1 if combo_counter % 3 == 0 else 0)
                        level += bonus
                    else:
                        combo_counter = 0
                        level += 1

                    if level > highscore:
                        highscore = level
                        save_highscore(highscore)

            if combo_counter >= 1:
                draw_text(f"Combo: {combo_counter}", GOLD, center=False, pos=(10, 160))

            pygame.display.flip()
            clock.tick(FPS)

        # Draw final state to show the result
        screen.blit(background_img, (0, 0))
        draw_ground()
        pygame.draw.rect(screen, BLACK, (elevator_x, elevator_y, elevator_width, elevator_height), 3)
        pygame.draw.rect(screen, RED, (player_x, player_y, player_size, player_size))

        if survived:
            draw_text("You Survived!", GREEN)
            if perfect_jump:
                draw_text("Perfect!", GOLD, y_offset=50, size=40)
                spark_frames = 10
                # Pulse effect
                for i in range(8):
                    glow = pygame.Surface((player_size + 20, player_size + 20), pygame.SRCALPHA)
                    glow.fill((255, 215, 0, 100 - i * 10))
                    screen.blit(glow, (player_x - 10, player_y - 10))
                    pygame.display.flip()
                    clock.tick(30)

        else:
            draw_text("Smashed!", RED)
            impact_sound.play()
            draw_text(f"You reached level {level}", BLACK, 40)
            if level > highscore:
                draw_text("New High Score!", GOLD, 80)
                spark_frames = 20
            else:
                pass
                #spark_frames = 10
            level = 1
            combo_counter = 0

        while spark_frames > 0:
            for _ in range(20):
                pygame.draw.circle(screen, GOLD, (random.randint(100, 300), random.randint(300, 500)), random.randint(1, 4))
            spark_frames -= 1
            pygame.display.flip()
            clock.tick(FPS)

        wait_for_space()
        

async def main():
    show_welcome_modal()
    game_loop()
    await asyncio.sleep(0)

asyncio.run(main())