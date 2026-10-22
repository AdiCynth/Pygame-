HOW TO RUN (two devices on the same Wi-Fi):

DEVICE 1 (the host):
  1. Open PowerShell, run:  ipconfig
     Find your "IPv4 Address" (e.g. 192.168.1.15)
  2. Terminal 1:  python server.py
     (it will also print your LAN IP for you)
  3. Terminal 2:  python client.py
     (this connects as Player 1)

DEVICE 2 (the guest):
  1. Open PowerShell, run:
       python client.py 192.168.1.15
     (replace with Device 1's actual IP)

NOTES:
- If Windows shows a firewall popup, click "Allow access"
- Both players use W/S or Up/Down arrows in their own window
- Press SPACE to start, R to restart, ESC to quit
- Both devices must have Python and pygame installed
