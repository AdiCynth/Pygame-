import socket
import json
import pygame

SERVER_IP = "127.0.0.1"
PORT = 5555

WIDTH, HEIGHT = 1200, 750
PADDLE_WIDTH, PADDLE_HEIGHT = 14, 120
BALL_SIZE = 16
OBSTACLE_W, OBSTACLE_H = 24, 110

BG_COLOR = (18, 18, 24)
FG_COLOR = (235, 235, 240)
DIM_COLOR = (90, 90, 105)
OBSTACLE_COLOR = (130, 130, 150)
P1_COLOR = (90, 170, 255)
P2_COLOR = (255, 120, 120)

obstacles = []
for xf in (0.35, 0.65):
    for yf in (0.25, 0.75):
        obstacles.append(pygame.Rect(int(WIDTH * xf) - OBSTACLE_W // 2, int(HEIGHT * yf) - OBSTACLE_H // 2, OBSTACLE_W, OBSTACLE_H))


def send_msg(sock, data):
    sock.sendall(json.dumps(data).encode() + b'\n')


def recv_msgs(sock, buf):
    try:
        data = sock.recv(4096)
        if not data:
            return None, buf
        buf += data
    except BlockingIOError:
        pass
    except (ConnectionResetError, ConnectionAbortedError, OSError):
        return None, buf
    msgs = []
    while b'\n' in buf:
        line, buf = buf.split(b'\n', 1)
        if line:
            msgs.append(json.loads(line))
    return msgs, buf


def draw_text(surface, text, font, color, center):
    s = font.render(text, True, color)
    surface.blit(s, s.get_rect(center=center))


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    print(f"Connecting to {SERVER_IP}:{PORT}...")
    sock.connect((SERVER_IP, PORT))
    print("Connected! Waiting for player assignment...")

    buf = b''
    pid = None
    while pid is None:
        msgs, buf = recv_msgs(sock, buf)
        if msgs is None:
            print("Disconnected.")
            return
        for m in msgs:
            if "pid" in m:
                pid = m["pid"]

    key_label = "W / S" if pid == 1 else "Up / Down"
    print(f"You are Player {pid} — Controls: {key_label}")

    sock.setblocking(False)

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption(f"Pong - Player {pid} ({key_label})")
    clock = pygame.time.Clock()
    game_surface = pygame.Surface((WIDTH, HEIGHT))

    huge_font = pygame.font.SysFont("arial", 140, bold=True)
    big_font = pygame.font.SysFont("arial", 72, bold=True)
    mid_font = pygame.font.SysFont("arial", 36, bold=True)
    small_font = pygame.font.SysFont("arial", 24)

    gs = None
    running = True

    while running:
        action = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    action = "start"
                elif event.key == pygame.K_r:
                    action = "restart"

        keys = pygame.key.get_pressed()
        inp = 0
        if pid == 1:
            if keys[pygame.K_w]:
                inp += 1
            if keys[pygame.K_s]:
                inp -= 1
        else:
            if keys[pygame.K_UP]:
                inp += 1
            if keys[pygame.K_DOWN]:
                inp -= 1

        msg = {"i": inp}
        if action:
            msg["a"] = action
        try:
            send_msg(sock, msg)
        except (BrokenPipeError, ConnectionResetError, OSError):
            running = False
            break

        msgs, buf = recv_msgs(sock, buf)
        if msgs is None:
            running = False
            break
        if msgs:
            gs = msgs[-1]

        game_surface.fill(BG_COLOR)

        if gs is None:
            draw_text(game_surface, f"You are Player {pid} - Waiting for opponent...", mid_font, FG_COLOR, (WIDTH // 2, HEIGHT // 2))
            draw_text(game_surface, f"Your controls: {key_label}", small_font, DIM_COLOR, (WIDTH // 2, HEIGHT // 2 + 50))
        else:
            for y in range(0, HEIGHT, 30):
                pygame.draw.rect(game_surface, DIM_COLOR, (WIDTH // 2 - 2, y + 5, 4, 15))
            for block in obstacles:
                pygame.draw.rect(game_surface, OBSTACLE_COLOR, block, border_radius=4)
            draw_text(game_surface, str(gs["sl"]), big_font, P1_COLOR, (WIDTH // 4, 60))
            draw_text(game_surface, str(gs["sr"]), big_font, P2_COLOR, (WIDTH * 3 // 4, 60))

            lp = pygame.Rect(40, gs["lp"], PADDLE_WIDTH, PADDLE_HEIGHT)
            rp = pygame.Rect(WIDTH - 40 - PADDLE_WIDTH, gs["rp"], PADDLE_WIDTH, PADDLE_HEIGHT)
            pygame.draw.rect(game_surface, P1_COLOR, lp, border_radius=4)
            pygame.draw.rect(game_surface, P2_COLOR, rp, border_radius=4)

            ball = pygame.Rect(round(gs["bx"]), round(gs["by"]), BALL_SIZE, BALL_SIZE)
            pygame.draw.ellipse(game_surface, FG_COLOR, ball)

            if gs["st"] == "waiting":
                draw_text(game_surface, "PONG", big_font, FG_COLOR, (WIDTH // 2, HEIGHT // 2 - 60))
                c = P1_COLOR if pid == 1 else P2_COLOR
                draw_text(game_surface, f"You are Player {pid}  ({key_label})", mid_font, c, (WIDTH // 2, HEIGHT // 2 + 20))
                draw_text(game_surface, "Press SPACE to start", small_font, DIM_COLOR, (WIDTH // 2, HEIGHT // 2 + 70))
            elif gs["st"] == "playing" and gs["cd"] > 0:
                draw_text(game_surface, str(gs["cd"]), huge_font, FG_COLOR, (WIDTH // 2, HEIGHT // 2 - 120))
                draw_text(game_surface, "Get ready!", small_font, DIM_COLOR, (WIDTH // 2, HEIGHT // 2 - 40))
            elif gs["st"] == "game_over":
                c = P1_COLOR if gs["w"] == "Player 1" else P2_COLOR
                draw_text(game_surface, f"{gs['w']} wins!", big_font, c, (WIDTH // 2, HEIGHT // 2 - 30))
                draw_text(game_surface, "Press R to restart | ESC to quit", small_font, FG_COLOR, (WIDTH // 2, HEIGHT // 2 + 50))

        win_w, win_h = screen.get_size()
        scale = min(win_w / WIDTH, win_h / HEIGHT)
        scaled_w, scaled_h = int(WIDTH * scale), int(HEIGHT * scale)
        offset_x, offset_y = (win_w - scaled_w) // 2, (win_h - scaled_h) // 2
        scaled = pygame.transform.smoothscale(game_surface, (scaled_w, scaled_h))
        screen.fill((0, 0, 0))
        screen.blit(scaled, (offset_x, offset_y))
        pygame.display.flip()
        clock.tick(60)

    sock.close()
    pygame.quit()


if __name__ == "__main__":
    main()
