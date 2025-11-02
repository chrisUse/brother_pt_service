#!/usr/bin/env python3
"""
Brother PT-E550W - FastAPI Label Service
Professional REST API für Tech-Labels
"""

import sys
sys.path.insert(0, '/home/chris/test/brother_pt')

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from brother_pt.printer import BrotherPt
from brother_pt.cmd import MediaWidthToTapeMargin, PRINT_HEAD_PINS
from typing import Optional
import uvicorn
import os

# Pydantic Models für API
class CableLabelRequest(BaseModel):
    cable_type: str
    voltage: Optional[str] = None
    destination: Optional[str] = None
    color_code: Optional[str] = None

class DeviceLabelRequest(BaseModel):
    device_name: str
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    model: Optional[str] = None
    rack_unit: Optional[str] = None

class WarningLabelRequest(BaseModel):
    warning_text: str
    voltage: Optional[str] = None
    icon: Optional[str] = "⚠"

class PrintResponse(BaseModel):
    success: bool
    message: str
    filename: Optional[str] = None

class BrotherTechAPI:
    """Brother PT-E550W Label Printer Service"""
    
    def __init__(self):
        """Initialisiert Brother Printer"""
        try:
            self.printer = BrotherPt()
            self.tape_width = self.printer.media_width
            self.print_height = PRINT_HEAD_PINS - MediaWidthToTapeMargin.margin[self.tape_width] * 2
            self.is_ready = True
            print(f"✅ Brother PT-E550W bereit: {self.tape_width}mm Tape, {self.print_height}px hoch")
            
        except Exception as e:
            self.is_ready = False
            print(f"❌ Brother PT-E550W nicht verfügbar: {e}")
            raise HTTPException(status_code=503, detail=f"Drucker nicht verfügbar: {e}")
    
    def _load_fonts(self):
        """Lade System-Fonts oder Fallback"""
        try:
            return {
                'bold': ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 10),
                'normal': ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 8),
                'small': ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 6)
            }
        except:
            default_font = ImageFont.load_default()
            return {'bold': default_font, 'normal': default_font, 'small': default_font}
    
    def create_cable_label(self, request: CableLabelRequest) -> Image.Image:
        """Erstellt Kabel-Label für Elektriker"""
        
        # Dynamische Breite basierend auf Text
        label_width = max(180, min(len(request.cable_type) * 12, 350))
        
        # Brother Pixel-Logic: 0=weiß, 1=schwarz
        img = Image.new('1', (label_width, self.print_height), 0)
        draw = ImageDraw.Draw(img)
        fonts = self._load_fonts()
        
        y = 3
        
        # 1. KABEL-TYP (Haupttext, fett, zentriert)
        bbox = draw.textbbox((0, 0), request.cable_type, font=fonts['bold'])
        text_width = bbox[2] - bbox[0]
        x = (label_width - text_width) // 2
        draw.text((x, y), request.cable_type, fill=1, font=fonts['bold'])
        y += bbox[3] - bbox[1] + 2
        
        # 2. SPANNUNG (⚡ Symbol für Sichtbarkeit)
        if request.voltage and y + 10 < self.print_height:
            voltage_text = f"⚡ {request.voltage}"
            bbox = draw.textbbox((0, 0), voltage_text, font=fonts['normal'])
            x = (label_width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), voltage_text, fill=1, font=fonts['normal'])
            y += bbox[3] - bbox[1] + 1
        
        # 3. DESTINATION (Pfeil für Richtung)
        if request.destination and y + 8 < self.print_height:
            dest_text = f"→ {request.destination}"
            bbox = draw.textbbox((0, 0), dest_text, font=fonts['small'])
            x = (label_width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), dest_text, fill=1, font=fonts['small'])
            y += bbox[3] - bbox[1] + 1
        
        # 4. FARBCODE (falls Platz vorhanden)
        if request.color_code and y + 6 < self.print_height:
            # Automatisch kürzen falls zu lang
            color_text = request.color_code
            bbox = draw.textbbox((0, 0), color_text, font=fonts['small'])
            if bbox[2] - bbox[0] > label_width - 8:
                max_chars = (label_width - 20) // 5
                color_text = color_text[:max_chars] + "..." if len(color_text) > max_chars else color_text
            
            bbox = draw.textbbox((0, 0), color_text, font=fonts['small'])
            x = (label_width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), color_text, fill=1, font=fonts['small'])
        
        return img
    
    def create_device_label(self, request: DeviceLabelRequest) -> Image.Image:
        """Erstellt Geräte-Label für IT-Techniker"""
        
        label_width = max(200, min(len(request.device_name) * 10, 380))
        img = Image.new('1', (label_width, self.print_height), 0)
        draw = ImageDraw.Draw(img)
        fonts = self._load_fonts()
        
        y = 2
        
        # 1. DEVICE NAME (Haupttext, fett)
        bbox = draw.textbbox((0, 0), request.device_name, font=fonts['bold'])
        x = (label_width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), request.device_name, fill=1, font=fonts['bold'])
        y += bbox[3] - bbox[1] + 2
        
        # 2. IP-ADRESSE (wichtigste Info für IT)
        if request.ip_address and y + 9 < self.print_height:
            ip_text = f"IP: {request.ip_address}"
            bbox = draw.textbbox((0, 0), ip_text, font=fonts['normal'])
            x = (label_width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), ip_text, fill=1, font=fonts['normal'])
            y += bbox[3] - bbox[1] + 1
        
        # 3. MAC-ADRESSE (kurz, nur relevanter Teil)
        if request.mac_address and y + 7 < self.print_height:
            # Zeige nur letzten Teil der MAC für bessere Lesbarkeit
            mac_short = request.mac_address.replace(':', '')[-6:].upper()
            mac_text = f"MAC: ...{mac_short}"
            bbox = draw.textbbox((0, 0), mac_text, font=fonts['small'])
            x = (label_width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), mac_text, fill=1, font=fonts['small'])
            y += bbox[3] - bbox[1] + 1
        
        # 4. MODELL oder RACK UNIT
        additional_info = request.model or request.rack_unit
        if additional_info and y + 6 < self.print_height:
            # Automatisch kürzen für bessere Darstellung
            if len(additional_info) > 30:
                additional_info = additional_info[:27] + "..."
            
            bbox = draw.textbbox((0, 0), additional_info, font=fonts['small'])
            x = (label_width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), additional_info, fill=1, font=fonts['small'])
        
        return img
    
    def create_warning_label(self, request: WarningLabelRequest) -> Image.Image:
        """Erstellt Sicherheits-/Warnungs-Label"""
        
        label_width = max(160, min(len(request.warning_text) * 12, 320))
        img = Image.new('1', (label_width, self.print_height), 0)
        draw = ImageDraw.Draw(img)
        fonts = self._load_fonts()
        
        y = 4
        
        # 1. WARNUNG mit Symbolen (sehr auffällig)
        warning_full = f"{request.icon} {request.warning_text.upper()} {request.icon}"
        bbox = draw.textbbox((0, 0), warning_full, font=fonts['bold'])
        x = (label_width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), warning_full, fill=1, font=fonts['bold'])
        y += bbox[3] - bbox[1] + 3
        
        # 2. SPANNUNG (falls vorhanden, extra hervorgehoben)
        if request.voltage and y + 10 < self.print_height:
            voltage_text = f">>> {request.voltage} <<<"
            bbox = draw.textbbox((0, 0), voltage_text, font=fonts['normal'])
            x = (label_width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), voltage_text, fill=1, font=fonts['normal'])
        
        return img
    
    def print_label_image(self, image: Image.Image, label_type: str) -> PrintResponse:
        """Druckt Label und speichert PNG-Backup"""
        
        if not self.is_ready:
            raise HTTPException(status_code=503, detail="Drucker nicht bereit")
        
        try:
            # PNG-Backup erstellen
            timestamp = datetime.now().strftime("%m%d_%H%M%S")
            filename = f"tech_{label_type}_{timestamp}.png"
            image.save(filename, 'PNG')
            
            # Brother PT drucken (50px Margin = bewährt)
            print(f"🖨️ Drucke {label_type}-Label...")
            self.printer.print_image(image, 50)
            
            return PrintResponse(
                success=True,
                message=f"{label_type.capitalize()}-Label erfolgreich gedruckt",
                filename=filename
            )
            
        except Exception as e:
            print(f"❌ Druck-Fehler: {e}")
            raise HTTPException(status_code=500, detail=f"Druck fehlgeschlagen: {e}")

# FastAPI App initialisieren
app = FastAPI(
    title="Brother PT-E550W Tech Label API",
    description="Professional Label Printing für Elektriker & IT-Techniker",
    version="1.0.0"
)

# Global printer instance
printer_service = None

@app.on_event("startup")
async def startup_event():
    """Initialisiere Drucker beim Start"""
    global printer_service
    try:
        printer_service = BrotherTechAPI()
        print("🚀 FastAPI Tech Label Service gestartet!")
    except Exception as e:
        print(f"❌ Startup Fehler: {e}")

@app.get("/", tags=["Status"])
async def root():
    """API Übersicht und Status"""
    return {
        "service": "Brother PT-E550W Tech Label API",
        "version": "1.0.0",
        "printer_ready": printer_service.is_ready if printer_service else False,
        "tape_width_mm": printer_service.tape_width if printer_service else None,
        "endpoints": {
            "cable": "POST /print/cable - Kabel-Labels für Elektriker",
            "device": "POST /print/device - Geräte-Labels für IT-Techniker", 
            "warning": "POST /print/warning - Sicherheits-/Warn-Labels",
            "status": "GET /status - Drucker-Status",
            "docs": "GET /docs - Interactive API Documentation"
        }
    }

@app.get("/status", tags=["Status"])
async def get_printer_status():
    """Drucker-Status abfragen"""
    if not printer_service:
        raise HTTPException(status_code=503, detail="Service nicht initialisiert")
    
    return {
        "printer_ready": printer_service.is_ready,
        "tape_width_mm": printer_service.tape_width,
        "print_height_px": printer_service.print_height,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/print/cable", response_model=PrintResponse, tags=["Labels"])
async def print_cable_label(request: CableLabelRequest):
    """
    Druckt Kabel-Label für Elektriker
    
    - **cable_type**: Kabel-Typ (z.B. "NYM 3x1.5", "CAT6")
    - **voltage**: Spannung (z.B. "230V", "PoE") 
    - **destination**: Ziel (z.B. "Steckdose A1", "Switch Port 12")
    - **color_code**: Farbkodierung (z.B. "L1-Braun L2-Schwarz N-Blau")
    """
    if not printer_service:
        raise HTTPException(status_code=503, detail="Drucker-Service nicht verfügbar")
    
    image = printer_service.create_cable_label(request)
    return printer_service.print_label_image(image, "cable")

@app.post("/print/device", response_model=PrintResponse, tags=["Labels"])
async def print_device_label(request: DeviceLabelRequest):
    """
    Druckt Geräte-Label für IT-Techniker
    
    - **device_name**: Geräte-Name (z.B. "SW-Core-01", "SRV-DB-02")
    - **ip_address**: IP-Adresse (z.B. "192.168.1.100")
    - **mac_address**: MAC-Adresse (z.B. "aa:bb:cc:dd:ee:ff")
    - **model**: Geräte-Modell (z.B. "Cisco SG300-28")
    - **rack_unit**: Rack-Position (z.B. "19HE U15")
    """
    if not printer_service:
        raise HTTPException(status_code=503, detail="Drucker-Service nicht verfügbar")
    
    image = printer_service.create_device_label(request)
    return printer_service.print_label_image(image, "device")

@app.post("/print/warning", response_model=PrintResponse, tags=["Labels"])
async def print_warning_label(request: WarningLabelRequest):
    """
    Druckt Sicherheits-/Warn-Label
    
    - **warning_text**: Warntext (z.B. "HOCHSPANNUNG", "NICHT ABSCHALTEN")
    - **voltage**: Spannung (z.B. "400V", "230V")
    - **icon**: Warn-Symbol (z.B. "⚠", "⚡", "🔥", "☠")
    """
    if not printer_service:
        raise HTTPException(status_code=503, detail="Drucker-Service nicht verfügbar")
    
    image = printer_service.create_warning_label(request)
    return printer_service.print_label_image(image, "warning")

if __name__ == "__main__":
    print("🚀 Starting Brother PT-E550W FastAPI Service...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Alternative Docs: http://localhost:8000/redoc")
    print("⚡ Service Info: http://localhost:8000/")
    
    uvicorn.run(
        "brother_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable in production
        log_level="info"
    )