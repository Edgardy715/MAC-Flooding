![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python) ![Scapy](https://img.shields.io/badge/Scapy-2.x-green) ![GNS3](https://img.shields.io/badge/GNS3-vIOS--L2-orange) ![Lab](https://img.shields.io/badge/Lab-EGALDITO__LAB-red)

# MAC Flooding Attack

> **Autor:** Edgardy Olivero | **Matricula:** 20250704  
> **Laboratorio:** EGALDITO_LAB | **Herramienta:** Python 3 + Scapy  
> **Repositorio:** [github.com/Edgardy715/MAC-Flooding](https://github.com/Edgardy715/MAC-Flooding)

---

## Objetivo del Laboratorio

Demostrar como un atacante puede saturar la tabla CAM (Content Addressable Memory) de un switch enviando frames Ethernet con MACs de origen falsas y aleatorias a alta velocidad, forzando al switch a comportarse como un hub y retransmitir el trafico a todos los puertos, lo que permite la captura pasiva del trafico de otros hosts. El ataque de MAC flooding busca precisamente llenar la tabla de direcciones del switch hasta provocar un comportamiento de *fail-open* [web:23][web:25].

## Objetivo del Script

Generar y enviar frames Ethernet continuamente, cada uno con una MAC de origen y destino completamente aleatoria, para llenar la tabla CAM del switch hasta que no pueda registrar nuevas entradas legitimas y comience a inundar todos los puertos. Esto expone trafico unicast de otros equipos y permite validar la debilidad de la red frente a ataques de capa 2 [web:23][web:26].

---

## Estructura del Repositorio

```text
MAC-Flooding/
├── Script/
│   └── MAC-Flooding.py                   <- Script principal del ataque
├── Mitigacion/
│   └── Mitigacion-MAC-flooding.ios       <- Comandos Port Security (Cisco IOS)
├── Conf-Topologia/
│   └── scripts_bases_configs/
│       ├── R1.ios
│       ├── SW1-VTPSERVER.ios
│       └── SW2.ios
├── Topologia/
│   └── Topologia.png
└── README.md
```

---

## Parametros del Script

| Variable | Valor | Descripcion |
|---|---|---|
| `IFACE` | `eth0` | Interfaz directa, sin subinterfaz VLAN, usada para el ataque de capa 2. |
| `INTERVALO` | `0.001` | 1 ms entre frames, equivalente a aproximadamente 1000 frames por segundo. |
| `rand_mac()` | aleatorio | Genera una MAC de 6 bytes completamente aleatoria. |
| `Raw(load)` | `"X" * 18` | Padding minimo para completar un frame Ethernet valido. |
| `enviados` | lista[int] | Contador de frames enviados durante la ejecucion. |

---

## Requisitos

```bash
# Dependencias
pip install scapy

# Verificar interfaz eth0 activa y conectada al switch
ip link show eth0

# Ejecutar como root
sudo python3 Script/MAC-Flooding.py
```

---

## Funcionamiento del Script

### Flujo de ejecucion

```text
1. Verifica ejecucion como root.
2. Registra handlers SIGINT/SIGTERM para cleanup().
3. En un bucle principal:
   a. Genera una MAC de origen aleatoria.
   b. Genera una MAC de destino aleatoria.
   c. Construye un frame Ether / IP / UDP / Raw.
   d. Envía el frame con sendp().
   e. Incrementa el contador enviados.
   f. Cada 500 frames, imprime el total enviado.
4. Al presionar Ctrl+C, cleanup() muestra el total de frames enviados.
```

### Estructura del frame enviado

```text
[Ether]  src=MAC_aleatoria  dst=MAC_aleatoria
  [IP]    src=1.1.1.1       dst=2.2.2.2
    [UDP] sport=1234        dport=4321
      [Raw] load="X" * 18   (padding minimo Ethernet)
```

### Efecto en la tabla CAM del switch

```text
Estado normal:
  MAC              VLAN  Puerto
  0c:bf:c5:c2:00   10    Gi0/1
  0cc0.7fb8.0000   1     Gi0/0

Durante el ataque:
  02:a1:b2:c3:d4   1     Gi0/1
  02:e5:f6:07:08   1     Gi0/1
  ... miles de MACs falsas ...

Consecuencia:
  El switch agota su tabla CAM y comienza a inundar todos los puertos.
  El atacante puede capturar trafico unicast de otros hosts.
```

### Verificacion en el switch durante el ataque

```cisco
SW2# show mac address-table count
SW2# show mac address-table | head 30
```

---

## Documentacion de la Red

### Topologia del Laboratorio

```text
+------------------+        +---------------------+        +---------------------+
|   Kali Linux     |        |        SW2          |        |        SW1          |
|   (Atacante)     |<------>|  GNS3 vIOS-L2       |<------>|  GNS3 vIOS-L2      |
|     eth0         |  Gi0/1 | VTP Client          |  Gi0/0 | VTP Server         |
| 0c:bf:c5:c2:00:00|        | 0cc0.7fb8.0000      |        | 0cb5.a4d7.0000    |
+------------------+        +---------------------+        +---------------------+
                                                                   |  Gi0/1
                                                        +---------------------+
                                                        |         R1          |
                                                        |  192.168.10.1/24    |
                                                        +---------------------+
```

> Topologia completa en `Topologia/Topologia.png`

### Tabla de Direccionamiento

| Dispositivo | Interfaz | VLAN | IP / Mascara | MAC | Rol |
|---|---|---:|---|---|---|
| Kali Linux | eth0 | 1 | dinamica | `0c:bf:c5:c2:00:00` | Atacante |
| SW1 | Gi0/0 (trunk) | 1,10 | — | `0cb5.a4d7.0000` | VTP Server / Root |
| SW2 | Gi0/0 (trunk) | 1,10 | — | `0cc0.7fb8.0000` | VTP Client |
| R1 | Gi0/0 | 10 | 192.168.10.1/24 | — | Gateway / DHCP |

```text
VTP Domain: EGALDITO_LAB | SW1: VTP Server | SW2: VTP Client
STP Root Bridge: SW1 | Priority: 32769 | MAC: 0cb5.a4d7.0000
VLAN 10: RED_LOCAL (192.168.10.0/24)
```

---

## Capturas de Pantalla

| Momento | Descripcion |
|---|---|
| Pre-ataque | `show mac address-table count` muestra pocas entradas legitimas. |
| Durante ataque | ~1000 frames/s, tabla CAM al limite de capacidad. |
| Efecto | El switch inunda todos los puertos, comportamiento similar a un hub. |
| Captura | Wireshark en Kali captura trafico unicast de otros hosts. |

---

## Contramedidas

El archivo de mitigacion esta en `Mitigacion/Mitigacion-MAC-flooding.ios`.

### 1. Port Security — defensa principal

```cisco
en
conf term
interface GigabitEthernet0/1
 switchport mode access
 switchport port-security
 switchport port-security maximum 5
 switchport port-security violation restrict
 switchport port-security violation shutdown
exit
do wr
```

### Verificacion

```cisco
SW2# show port-security interface GigabitEthernet0/1
SW2# show port-security address
```

`violation restrict` descarta frames no permitidos y registra el evento; `violation shutdown` desactiva el puerto si se excede el limite. Port Security es la mitigacion clasica para ataques de overflow de tabla CAM [web:22][web:24][web:27].

### 2. MAC address sticky

```cisco
interface GigabitEthernet0/1
 switchport port-security mac-address sticky
```

---

## Video Demostrativo

**Lista de reproduccion EGALDITO_LAB:** [Layer 2 Network Attacks](https://www.youtube.com/@Edgardy715)

---

*Laboratorio desarrollado con fines estrictamente educativos en entorno GNS3 aislado.*  
*Autor: Edgardy Olivero | 20250704 | EGALDITO_LAB*
