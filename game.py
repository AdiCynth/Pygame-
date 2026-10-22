import random
import pygame

WIDTH, HEIGHT = 1200, 750
FPS = 60
PADDLE_WIDTH, PADDLE_HEIGHT = 14, 120
PADDLE_SPEED = 8
BALL_SIZE = 16
BALL_START_SPEED = 6
BALL_MAX_SPEED = 14
WINNING_SCORE = 5
COUNTDOWN_SECONDS = 5

BG_COLOR = (18, 18, 24)
FG_COLOR = (235, 235, 240)
DIM_COLOR = (90, 90, 105)
OBSTACLE_COLOR = (130, 130, 150)
P1_COLOR = (90, 170, 255)
P2_COLOR = (255, 120, 120)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong - 2 Players")
clock = pygame.time.Clock()

huge_font = pygame.font.SysFont("arial", 140, bold=True)
big_font = pygame.font.SysFont("arial", 72, bold=True)
mid_font = pygame.font.SysFont("arial", 36, bold=True)
small_font = pygame.font.SysFont("arial", 24)

left_paddle = pygame.Rect(40, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
right_paddle = pygame.Rect(WIDTH - 40 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
ball = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)

OBSTACLE_W, OBSTACLE_H = 24, 110
obstacles = []
for x_frac in (0.35, 0.65):
    for y_frac in (0.25, 0.75):
        block = pygame.Rect(0, 0, OBSTACLE_W, OBSTACLE_H)
        block.center = (int(WIDTH * x_frac), int(HEIGHT * y_frac))
        obstacles.append(block)

ball_x, ball_y = 0.0, 0.0
ball_dx, ball_dy = 0.0, 0.0
score_left = 0
score_right = 0
state = "start"
winner = ""
serve_time = 0


def reset_ball(direction):
    global ball_x, ball_y, ball_dx, ball_dy, serve_time
    ball_x = WIDTH / 2 - BALL_SIZE / 2
    ball_y = HEIGHT / 2 - BALL_SIZE / 2
    ball_dx = BALL_START_SPEED * direction
    ball_dy = random.uniform(-3, 3)
    ball.topleft = (ball_x, ball_y)
    serve_time = pygame.time.get_ticks() + COUNTDOWN_SECONDS * 1000


def reset_game():
    global score_left, score_right
    score_left = 0
    score_right = 0
    left_paddle.centery = HEIGHT // 2
    right_paddle.centery = HEIGHT // 2
    reset_ball(random.choice([-1, 1]))


def countdown_left():
    ms = serve_time - pygame.time.get_ticks()
    if ms <= 0:
        return 0
    return (ms + 999) // 1000


def bounce_off_paddle(paddle):
    global ball_dx, ball_dy
    offset = (ball.centery - paddle.centery) / (PADDLE_HEIGHT / 2)
    speed = min(abs(ball_dx) + 0.5, BALL_MAX_SPEED)
    ball_dx = speed if ball_dx < 0 else -speed
    ball_dy = offset * 7


def bounce_off_obstacle(block):
    global ball_x, ball_y, ball_dx, ball_dy
    overlap_x = min(ball.right - block.left, block.right - ball.left)
    overlap_y = min(ball.bottom - block.top, block.bottom - ball.top)
    if overlap_x < overlap_y:
        if ball.centerx < block.centerx:
            ball.right = block.left
            ball_dx = -abs(ball_dx)
        else:
            ball.left = block.right
            ball_dx = abs(ball_dx)
    else:
        if ball.centery < block.centery:
            ball.bottom = block.top
            ball_dy = -abs(ball_dy)
        else:
            ball.top = block.bottom
            ball_dy = abs(ball_dy)
    ball_x, ball_y = ball.x, ball.y


def draw_text(text, font, color, center):
    surface = font.render(text, True, color)
    rect = surface.get_rect(center=center)
    screen.blit(surface, rect)


def draw_court():
    screen.fill(BG_COLOR)
    for y in range(0, HEIGHT, 30):
        pygame.draw.rect(screen, DIM_COLOR, (WIDTH // 2 - 2, y + 5, 4, 15))
    for block in obstacles:
        pygame.draw.rect(screen, OBSTACLE_COLOR, block, border_radius=4)
    draw_text(str(score_left), big_font, P1_COLOR, (WIDTH // 4, 60))
    draw_text(str(score_right), big_font, P2_COLOR, (WIDTH * 3 // 4, 60))


def draw_start_screen():
    screen.fill(BG_COLOR)
    draw_text("PONG", big_font, FG_COLOR, (WIDTH // 2, 180))
    draw_text("Player 1:  W / S", small_font, P1_COLOR, (WIDTH // 2, 300))
    draw_text("Player 2:  Up / Down", small_font, P2_COLOR, (WIDTH // 2, 340))
    draw_text(f"First to {WINNING_SCORE} points wins  -  watch out for the obstacles", small_font, DIM_COLOR, (WIDTH // 2, 390))
    draw_text("Press SPACE to start", mid_font, FG_COLOR, (WIDTH // 2, 520))


def draw_game():
    draw_court()
    pygame.draw.rect(screen, P1_COLOR, left_paddle, border_radius=4)
    pygame.draw.rect(screen, P2_COLOR, right_paddle, border_radius=4)
    pygame.draw.ellipse(screen, FG_COLOR, ball)
    seconds = countdown_left()
    if seconds > 0:
        draw_text(str(seconds), huge_font, FG_COLOR, (WIDTH // 2, HEIGHT // 2 - 120))
        draw_text("Get ready!", small_font, DIM_COLOR, (WIDTH // 2, HEIGHT // 2 - 40))


def draw_game_over():
    draw_court()
    color = P1_COLOR if winner == "Player 1" else P2_COLOR
    draw_text(f"{winner} wins!", big_font, color, (WIDTH // 2, HEIGHT // 2 - 30))
    draw_text("Press R to restart  |  ESC to quit", small_font, FG_COLOR, (WIDTH // 2, HEIGHT // 2 + 50))


def move_paddles():
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        left_paddle.y -= PADDLE_SPEED
    if keys[pygame.K_s]:
        left_paddle.y += PADDLE_SPEED
    if keys[pygame.K_UP]:
        right_paddle.y -= PADDLE_SPEED
    if keys[pygame.K_DOWN]:
        right_paddle.y += PADDLE_SPEED
    left_paddle.clamp_ip(screen.get_rect())
    right_paddle.clamp_ip(screen.get_rect())


def move_ball():
    global ball_x, ball_y, ball_dy, score_left, score_right, state, winner
    if countdown_left() > 0:
        return
    ball_x += ball_dx
    ball_y += ball_dy
    ball.topleft = (round(ball_x), round(ball_y))
    if ball.top <= 0:
        ball_y = 0
        ball_dy = abs(ball_dy)
    elif ball.bottom >= HEIGHT:
        ball_y = HEIGHT - BALL_SIZE
        ball_dy = -abs(ball_dy)
    for block in obstacles:
        if ball.colliderect(block):
            bounce_off_obstacle(block)
            break
    if ball.colliderect(left_paddle) and ball_dx < 0:
        bounce_off_paddle(left_paddle)
    elif ball.colliderect(right_paddle) and ball_dx > 0:
        bounce_off_paddle(right_paddle)
    if ball.right < 0:
        score_right += 1
        reset_ball(-1)
    elif ball.left > WIDTH:
        score_left += 1
        reset_ball(1)
    if score_left >= WINNING_SCORE:
        winner = "Player 1"
        state = "game_over"
    elif score_right >= WINNING_SCORE:
        winner = "Player 2"
        state = "game_over"


def main():
    global state
    reset_game()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE and state == "start":
                    reset_game()
                    state = "playing"
                elif event.key == pygame.K_r and state == "game_over":
                    reset_game()
                    state = "playing"
        if state == "start":
            draw_start_screen()
        elif state == "playing":
            move_paddles()
            move_ball()
            draw_game()
        elif state == "game_over":
            draw_game_over()
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    main()
