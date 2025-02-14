import network
import socket
import machine
import time
import os
from picographics import PicoGraphics, DISPLAY_PICO_DISPLAY_2, PEN_P4
from jpegdec import JPEG
from secrets import secrets

machine.freq(150000000)

# Setup onboard LED and LCD state
led = machine.Pin("LED", machine.Pin.OUT)
LedState = 'OFF'

# Initialize Pimoroni Pico Display
pico_display = PicoGraphics(display=DISPLAY_PICO_DISPLAY_2, pen_type=PEN_P4)
pico_display.set_backlight(1)
WHITE = pico_display.create_pen(255, 255, 255)
RED = pico_display.create_pen(255, 0, 0)
GREEN = pico_display.create_pen(0, 255, 0)
BLUE = pico_display.create_pen(0, 0, 255)
BLACK = pico_display.create_pen(0, 0, 0)

WIDTH, HEIGHT = 320, 240

pico_display.set_pen(BLACK)
pico_display.update()

def webpage(led_state):
    image = "pico_on.jpg" if led_state == 'ON' else "pico_off.jpg"
    return f"""<!DOCTYPE html>
    <html>
    <head>
        <title>Pico W LED Control</title>
        <style>
            body {{text-align: center; margin: 0; height: 220px; display: flex; justify-content: center; align-items: center; }}
            .frame {{ border: 3px solid black; padding:20px; display: flex; flex-direction: column; align-items: center; max-width: 320px; }}
            .content {{ display: flex; align-items: center; }}
            .controls {{ display: flex; flex-direction: column; align-items: center; }}
            button {{ font-size: 20px; padding: 10px; width: 120px; height: 41px; border: black; cursor: pointer; }}
            .on {{ background-color: green; color: white; }}
            .off {{ background-color: red; color: black; }}
            img {{ width: 200px; height: auto; margin-left: 0px; }}
            h2 {{ font-size: 20px; color: black; text-align: center; width: 100%; margin-bottom: 15px; }}
        </style>
    </head>
    <body>
        <div class="frame">
            <h2 style="margin-top: -5px;">Controlling the onboard green LED</h2>
            <div class="content">
                <div class="controls">
                    <form action="on"><button class="on">Turn ON</button></form>
                    <form action="off"><button class="off">Turn OFF</button></form>
                </div>
                <img src="/{image}" alt="Pico W">
            </div>
        </div>
    </body>
    </html>"""


def update_display():
    """ Updates the Pico Display with text and displays the image. """
    pico_display.clear()
    pico_display.set_pen(BLUE)
    clock_speed_mhz = machine.freq() // 1_000_000
    pico_display.text(f"Clock Speed: {clock_speed_mhz} MHz", 0, 0, WIDTH, 1)
    pico_display.set_pen(WHITE)
    pico_display.text("Pico W IP:", 110, 0, WIDTH, 1)
    pico_display.text(ip_address, 160, 0, WIDTH, 1)
    pico_display.set_pen(GREEN if LedState == 'ON' else RED)
    pico_display.text("LED: " + LedState, 235, 0, WIDTH, 1)
    pico_display.set_pen(BLACK)
    pico_display.update()

# Wi-Fi Connection
ssid = secrets['SSID']
password = secrets['PASSWORD']

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

max_wait = 10
while not wlan.isconnected():
    if max_wait <= 0:
        update_display()
        break
    max_wait -= 1
    time.sleep(2)

ip_address = wlan.ifconfig()[0]
print("Connected to WiFi, IP:", ip_address)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("", 80))
s.listen(5)

while True:
    update_display()
    conn, addr = s.accept()
    request = conn.recv(1024).decode()
    print("Request:", request)

    if "GET /on" in request:
        led.value(1)
        LedState = "ON"
    elif "GET /off" in request:
        led.value(0)
        LedState = "OFF"
    elif "GET /pico_on.jpg" in request:
        try:
            with open("pico_on.jpg", "rb") as f:
                image_data = f.read()
            conn.send("HTTP/1.1 200 OK\nContent-Type: image/jpeg\n\n".encode())
            conn.sendall(image_data)
        except Exception as e:
            print("Error serving image:", e)
        conn.close()
        continue
    elif "GET /pico_off.jpg" in request:
        try:
            with open("pico_off.jpg", "rb") as f:
                image_data = f.read()
            conn.send("HTTP/1.1 200 OK\nContent-Type: image/jpeg\n\n".encode())
            conn.sendall(image_data)
        except Exception as e:
            print("Error serving image:", e)
        conn.close()
        continue

    response = webpage(LedState)
    conn.send("HTTP/1.1 200 OK\nContent-Type: text/html\n\n" + response)
    conn.close()
