import socket
import json
import time
import random

HOST = "0.0.0.0"
PORT = 5555
TICK_RATE = 60

WIDTH, HEIGHT = 1200, 750
PADDLE_WIDTH, PADDLE_HEIGHT = 14, 120
PADDLE_SPEED = 8
BALL_SIZE = 16
BALL_START_SPEED = 6
BALL_MAX_SPEED = 14
WINNING_SCORE = 5
COUNTDOWN_SECONDS = 5
OBSTACLE_W, OBSTACLE_H = 24, 110

obstacles = []
for xf in (0.35, 0.65):
    for yf in (0.25, 0.75):
        obstacles.append((int(WIDTH * xf) - OBSTACLE_W // 2, int(HEIGHT * yf) - OBSTACLE_H // 2, OBSTACLE_W, OBSTACLE_H))


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def collide(a, b):
    return a[0] < b[0] + b[2] and a[0] + a[2] > b[0] and a[1] < b[1] + b[3] and a[1] + a[3] > b[1]


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


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.lp = HEIGHT // 2 - PADDLE_HEIGHT // 2
        self.rp = HEIGHT // 2 - PADDLE_HEIGHT // 2
        self.sl = 0
        self.sr = 0
        self.state = "waiting"
        self.winner = ""
        self.reset_ball(random.choice([-1, 1]))

    def reset_ball(self, d):
        self.bx = WIDTH / 2 - BALL_SIZE / 2
        self.by = HEIGHT / 2 - BALL_SIZE / 2
        self.bdx = BALL_START_SPEED * d
        self.bdy = random.uniform(-3, 3)
        self.serve_time = time.time() + COUNTDOWN_SECONDS

    def countdown(self):
        r = self.serve_time - time.time()
        return max(0, int(r) + 1) if r > 0 else 0

    def update(self, p1i, p2i, p1a, p2a):
        if self.state == "waiting":
            if p1a == "start" or p2a == "start":
                self.reset()
                self.state = "playing"
            return
        if self.state == "game_over":
            if p1a == "restart" or p2a == "restart":
                self.reset()
                self.state = "playing"
            return

        self.lp -= p1i * PADDLE_SPEED
        self.lp = max(0, min(HEIGHT - PADDLE_HEIGHT, self.lp))
        self.rp -= p2i * PADDLE_SPEED
        self.rp = max(0, min(HEIGHT - PADDLE_HEIGHT, self.rp))

        if self.countdown() > 0:
            return

        self.bx += self.bdx
        self.by += self.bdy

        if self.by <= 0:
            self.by = 0
            self.bdy = abs(self.bdy)
        elif self.by + BALL_SIZE >= HEIGHT:
            self.by = HEIGHT - BALL_SIZE
            self.bdy = -abs(self.bdy)

        br = (round(self.bx), round(self.by), BALL_SIZE, BALL_SIZE)
        for obs in obstacles:
            if collide(br, obs):
                self.bounce_obs(obs)
                break

        lpr = (40, self.lp, PADDLE_WIDTH, PADDLE_HEIGHT)
        rpr = (WIDTH - 40 - PADDLE_WIDTH, self.rp, PADDLE_WIDTH, PADDLE_HEIGHT)
        br = (round(self.bx), round(self.by), BALL_SIZE, BALL_SIZE)

        if collide(br, lpr) and self.bdx < 0:
            self.bounce_paddle(self.lp, 1)
        elif collide(br, rpr) and self.bdx > 0:
            self.bounce_paddle(self.rp, -1)

        if self.bx + BALL_SIZE < 0:
            self.sr += 1
            self.check_winner()
            if self.state == "playing":
                self.reset_ball(-1)
        elif self.bx > WIDTH:
            self.sl += 1
            self.check_winner()
            if self.state == "playing":
                self.reset_ball(1)

    def bounce_obs(self, obs):
        bx, by = round(self.bx), round(self.by)
        ox, oy, ow, oh = obs
        ovx = min(bx + BALL_SIZE - ox, ox + ow - bx)
        ovy = min(by + BALL_SIZE - oy, oy + oh - by)
        if ovx < ovy:
            if bx + BALL_SIZE / 2 < ox + ow / 2:
                self.bx = ox - BALL_SIZE
                self.bdx = -abs(self.bdx)
            else:
                self.bx = ox + ow
                self.bdx = abs(self.bdx)
        else:
            if by + BALL_SIZE / 2 < oy + oh / 2:
                self.by = oy - BALL_SIZE
                self.bdy = -abs(self.bdy)
            else:
                self.by = oy + oh
                self.bdy = abs(self.bdy)

    def bounce_paddle(self, py, direction):
        offset = (self.by + BALL_SIZE / 2 - (py + PADDLE_HEIGHT / 2)) / (PADDLE_HEIGHT / 2)
        speed = min(abs(self.bdx) + 0.5, BALL_MAX_SPEED)
        self.bdx = speed * direction
        self.bdy = offset * 7

    def check_winner(self):
        if self.sl >= WINNING_SCORE:
            self.winner = "Player 1"
            self.state = "game_over"
        elif self.sr >= WINNING_SCORE:
            self.winner = "Player 2"
            self.state = "game_over"

    def to_dict(self):
        return {
            "lp": round(self.lp), "rp": round(self.rp),
            "bx": round(self.bx, 1), "by": round(self.by, 1),
            "sl": self.sl, "sr": self.sr,
            "st": self.state, "w": self.winner,
            "cd": self.countdown()
        }


def main():
    local_ip = get_local_ip()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT))
    srv.listen(2)
    print(f"Server listening on all interfaces, port {PORT}")
    print(f"Your LAN IP: {local_ip}")
    print(f"Tell the other player to run:  python client.py {local_ip}")
    print("Waiting for 2 players...")

    c1, a1 = srv.accept()
    c1.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    print(f"Player 1 connected: {a1}")
    send_msg(c1, {"pid": 1})

    c2, a2 = srv.accept()
    c2.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    print(f"Player 2 connected: {a2}")
    send_msg(c2, {"pid": 2})

    c1.setblocking(False)
    c2.setblocking(False)

    game = Game()
    b1, b2 = b'', b''
    p1i, p2i = 0, 0

    print("Both players connected. Game running.")

    while True:
        t = time.time()
        p1a, p2a = None, None

        m1, b1 = recv_msgs(c1, b1)
        m2, b2 = recv_msgs(c2, b2)

        if m1 is None or m2 is None:
            print("Player disconnected.")
            break

        for m in m1:
            p1i = m.get("i", 0)
            if "a" in m:
                p1a = m["a"]
        for m in m2:
            p2i = m.get("i", 0)
            if "a" in m:
                p2a = m["a"]

        game.update(p1i, p2i, p1a, p2a)
        st = game.to_dict()

        try:
            send_msg(c1, st)
            send_msg(c2, st)
        except (BrokenPipeError, ConnectionResetError, OSError):
            print("Player disconnected.")
            break

        elapsed = time.time() - t
        time.sleep(max(0, 1 / TICK_RATE - elapsed))

    c1.close()
    c2.close()
    srv.close()


if __name__ == "__main__":
    main()
