HOW TO RUN (two devices on the same Wi-Fi):

DEVICE 1 (host - your PC at 10.0.16.155):
  1. Terminal 1:  python server.py
  2. Terminal 2:  python client.py
     (connects as Player 1)

DEVICE 2 (guest / second device on same Wi-Fi):
  1. python client.py
     (defaults to 10.0.16.155, or explicitly: python client.py 10.0.16.155)

NOTES:
- If Windows shows a firewall popup, click "Allow access"
- Both players use W/S or Up/Down arrows in their own window
- Press SPACE to start, R to restart, ESC to quit
- Both devices must have Python and pygame installed
