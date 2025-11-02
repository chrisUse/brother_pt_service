# Brother PT Print Service

🏷️ **Professional Docker-basierter Label-Service für Brother PT-E550W**

Speziell entwickelt ## 🔧 Administration

### **Pure Docker-native Befehle:**
```bash
# Service Management
./deploy.sh start       # Service starten
./deploy.sh stop        # Service stoppen  
./deploy.sh restart     # Service neustarten
./deploy.sh status      # Status anzeigen
./deploy.sh logs        # Logs anzeigen (live)

# Development & Testing
./deploy.sh test        # API Tests ausführen
./deploy.sh shell       # Container Shell öffnen
./deploy.sh build       # Container neu bauen

# Maintenance
./deploy.sh clean       # Aufräumen
```

### **Docker Compose direkt:**
```bash
docker-compose ps       # Container Status
docker-compose logs -f  # Live Logs
docker-compose exec brother-label-api /bin/bash  # Shell
``` & IT-Techniker** mit REST API für automatisierte Label-Erstellung.

## 🎯 Features

### ⚡ **Elektriker-Labels:**
- **Kabel-Labels:** Typ, Spannung, Ziel, Farbkodierung
- **Sicherheits-Labels:** Warnungen, Hochspannung, Symbole

### 💻 **IT-Techniker-Labels:**  
- **Geräte-Labels:** Name, IP-Adresse, MAC, Modell
- **Netzwerk-Labels:** Switch-Ports, Server, Rack-Units

### 🚀 **Tech-Stack:**
- **FastAPI** - Moderne REST API
- **Docker** - Container-Deployment
- **Brother PT Protocol** - Direkte USB-Kommunikation
- **Nginx** - Reverse Proxy (optional)
- **Pydantic** - Request Validation

## 📋 Voraussetzungen

- **Docker** & **Docker Compose**
- **Brother PT-E550W** per USB verbunden
- **Linux Host** mit USB-Zugriff
- **Internet-Verbindung** (für GitHub Checkout beim Build)

## 🚀 Quick Start

### 1. Service starten:
```bash
cd BrotherPTPrintService
chmod +x deploy.sh
./deploy.sh start    # oder einfach ./deploy.sh
```

### 2. Service verwalten:
```bash
./deploy.sh status   # Status anzeigen
./deploy.sh logs     # Logs anzeigen
./deploy.sh test     # API Tests ausführen
./deploy.sh stop     # Service stoppen
```

### 3. Web-Interface öffnen:
- **API Dokumentation:** http://localhost:8000/docs
- **Alternative Docs:** http://localhost:8000/redoc
- **Service Status:** http://localhost:8000/

## 🔌 API Endpoints

### **POST /print/cable** - Kabel-Labels
Erstellt Labels für elektrische Kabel und Netzwerkkabel.

**Request:**
```json
{
  "cable_type": "NYM 3x1.5",
  "voltage": "230V",
  "destination": "Steckdose A1",
  "color_code": "L1-Braun L2-Schwarz N-Blau"
}
```

### **POST /print/device** - Geräte-Labels
Erstellt Labels für IT-Geräte und Netzwerk-Hardware.

**Request:**
```json
{
  "device_name": "SW-Core-01",
  "ip_address": "192.168.1.100",
  "mac_address": "aa:bb:cc:dd:ee:ff",
  "model": "Cisco SG300-28",
  "rack_unit": "19HE U15"
}
```

### **POST /print/warning** - Warn-Labels
Erstellt Sicherheits- und Warnungs-Labels.

**Request:**
```json
{
  "warning_text": "HOCHSPANNUNG",
  "voltage": "400V",
  "icon": "⚡"
}
```

### **GET /status** - Service Status
```json
{
  "printer_ready": true,
  "tape_width_mm": 9,
  "print_height_px": 50,
  "container_id": "abc123",
  "timestamp": "2025-11-02T13:30:00"
}
```

## 🛠️ Konfiguration

### **docker-compose.yml**
```yaml
services:
  brother-label-api:
    build: .
    ports:
      - "8000:8000"
    devices:
      - "/dev/bus/usb:/dev/bus/usb"  # USB-Zugriff
    volumes:
      - "./labels:/app/labels"       # Label-Backups
```

### **Environment Variables**
- `PYTHONUNBUFFERED=1` - Python Output Buffering
- Standard FastAPI/Uvicorn Konfiguration

## 📊 Monitoring

### **Container Status:**
```bash
docker-compose ps
```

### **Logs anzeigen:**
```bash
docker-compose logs -f brother-label-api
```

### **Health Check:**
```bash
curl http://localhost:8000/status
```

## 🔧 Administration

### **Service stoppen:**
```bash
docker-compose down
```

### **Service neustarten:**
```bash
docker-compose restart
```

### **Image neu bauen:**
```bash
docker-compose build --no-cache
```

### **Logs leeren:**
```bash
docker-compose down
docker system prune -f
```

## 📁 Projektstruktur

```
BrotherPTPrintService/
├── brother_docker_api.py    # Haupt-API Service
├── brother_fastapi.py       # Alternative FastAPI Version
├── Dockerfile               # Container Definition (clont brother_pt)
├── docker-compose.yml       # Multi-Service Setup
├── requirements.txt         # Python Dependencies
├── nginx.conf              # Reverse Proxy Config
├── deploy.sh               # Deployment Script
├── labels/                 # Label-Backup Ordner
├── .dockerignore           # Docker Build Excludes
└── README.md               # Diese Dokumentation

Note: brother_pt/ wird automatisch aus GitHub geclont
```

## 🚨 Troubleshooting

### **Drucker nicht erkannt:**
```bash
# USB-Geräte prüfen
lsusb | grep Brother

# Container USB-Zugriff prüfen
docker-compose exec brother-label-api lsusb
```

### **Permission Denied:**
```bash
# User zu dialout Gruppe hinzufügen
sudo usermod -a -G dialout $USER

# Docker ohne sudo ausführen
sudo usermod -a -G docker $USER
```

### **Port bereits belegt:**
```yaml
# In docker-compose.yml Port ändern
ports:
  - "8080:8000"  # Externer Port 8080
```

## 🔒 Sicherheit

### **Production Deployment:**
- CORS Origins einschränken
- HTTPS mit SSL Zertifikaten
- API Rate Limiting
- Container Security Best Practices

### **Firewall:**
```bash
# Nur lokale API-Zugriffe
iptables -A INPUT -p tcp --dport 8000 -s 192.168.0.0/16 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP
```

## 📈 Performance

- **Single Worker** - Optimiert für USB-Drucker
- **Health Checks** - Automatische Überwachung  
- **Graceful Shutdown** - Sauberes Container-Stop
- **Resource Limits** - Memory/CPU Begrenzung möglich

## 🤝 Integration Beispiele

### **Python Client:**
```python
import requests

def print_cable_label(cable_type, voltage, destination):
    response = requests.post('http://localhost:8000/print/cable', json={
        'cable_type': cable_type,
        'voltage': voltage, 
        'destination': destination
    })
    return response.json()
```

### **Bash Script:**
```bash
#!/bin/bash
print_device_label() {
    curl -X POST http://localhost:8000/print/device \
        -H 'Content-Type: application/json' \
        -d "{\"device_name\":\"$1\",\"ip_address\":\"$2\"}"
}
```

## 📞 Support

- **GitHub Issues** für Bugs und Feature Requests  
- **API Dokumentation:** http://localhost:8000/docs
- **Brother PT-E550W Handbuch** für Hardware-Spezifikationen

---

**🏷️ Brother PT Print Service - Professional Label Printing Made Easy!**