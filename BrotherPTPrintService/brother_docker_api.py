#!/usr/bin/env python3
"""
Brother PT-E550W - Docker FastAPI Label Service
Optimiert für Container-Deployment
"""

import sys
sys.path.insert(0, '/app/brother_pt')

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from brother_pt.printer import BrotherPt
from brother_pt.cmd import MediaWidthToTapeMargin, PRINT_HEAD_PINS
from typing import Optional
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models
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

class TextLabelRequest(BaseModel):
    text: str
    font_size: Optional[int] = 14  # Größere Standardschrift

class PrintResponse(BaseModel):
    success: bool
    message: str
    filename: Optional[str] = None

class BrotherDockerAPI:
    """Docker-optimized Brother PT-E550W Service"""
    
    def __init__(self):
        """Initialize Brother Printer with Docker considerations"""
        self.is_ready = False
        self.tape_width = 9  # Default
        self.print_height = 50  # Default
        
        try:
            # Retry logic for Docker startup
            import time
            max_retries = 5
            
            for attempt in range(max_retries):
                try:
                    self.printer = BrotherPt()
                    self.tape_width = self.printer.media_width
                    self.print_height = PRINT_HEAD_PINS - MediaWidthToTapeMargin.margin[self.tape_width] * 2
                    self.is_ready = True
                    logger.info(f"✅ Brother PT-E550W ready: {self.tape_width}mm tape, {self.print_height}px height")
                    break
                    
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        logger.error("❌ Brother PT-E550W initialization failed after all retries")
                        # Continue without printer for API documentation access
                        
        except Exception as e:
            logger.error(f"❌ Critical error during printer initialization: {e}")
    
    def _get_fonts(self):
        """Load Docker-compatible fonts"""
        try:
            return {
                'bold': ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 10),
                'normal': ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 8),
                'small': ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 6)
            }
        except Exception as e:
            logger.warning(f"Font loading failed, using default: {e}")
            default = ImageFont.load_default()
            return {'bold': default, 'normal': default, 'small': default}
    
    def create_cable_label(self, request: CableLabelRequest) -> Image.Image:
        """Create cable label for electricians"""
        label_width = max(180, min(len(request.cable_type) * 12, 350))
        img = Image.new('1', (label_width, self.print_height), 0)
        draw = ImageDraw.Draw(img)
        fonts = self._get_fonts()
        
        y = 3
        
        # Cable type (main text)
        bbox = draw.textbbox((0, 0), request.cable_type, font=fonts['bold'])
        x = (label_width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), request.cable_type, fill=1, font=fonts['bold'])
        y += bbox[3] - bbox[1] + 2
        
        # Voltage
        if request.voltage and y + 10 < self.print_height:
            voltage_text = f"⚡ {request.voltage}"
            bbox = draw.textbbox((0, 0), voltage_text, font=fonts['normal'])
            x = (label_width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), voltage_text, fill=1, font=fonts['normal'])
            y += bbox[3] - bbox[1] + 1
        
        # Destination
        if request.destination and y + 8 < self.print_height:
            dest_text = f"→ {request.destination}"
            bbox = draw.textbbox((0, 0), dest_text, font=fonts['small'])
            x = (label_width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), dest_text, fill=1, font=fonts['small'])
            y += bbox[3] - bbox[1] + 1
        
        # Color code
        if request.color_code and y + 6 < self.print_height:
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
        """Create device label for IT technicians"""
        label_width = max(200, min(len(request.device_name) * 10, 380))
        img = Image.new('1', (label_width, self.print_height), 0)
        draw = ImageDraw.Draw(img)
        fonts = self._get_fonts()
        
        y = 2
        
        # Device name
        bbox = draw.textbbox((0, 0), request.device_name, font=fonts['bold'])
        x = (label_width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), request.device_name, fill=1, font=fonts['bold'])
        y += bbox[3] - bbox[1] + 2
        
        # IP address
        if request.ip_address and y + 9 < self.print_height:
            ip_text = f"IP: {request.ip_address}"
            bbox = draw.textbbox((0, 0), ip_text, font=fonts['normal'])
            x = (label_width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), ip_text, fill=1, font=fonts['normal'])
            y += bbox[3] - bbox[1] + 1
        
        # MAC address (short version)
        if request.mac_address and y + 7 < self.print_height:
            mac_short = request.mac_address.replace(':', '')[-6:].upper()
            mac_text = f"MAC: ...{mac_short}"
            bbox = draw.textbbox((0, 0), mac_text, font=fonts['small'])
            x = (label_width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), mac_text, fill=1, font=fonts['small'])
            y += bbox[3] - bbox[1] + 1
        
        # Model or rack unit
        additional_info = request.model or request.rack_unit
        if additional_info and y + 6 < self.print_height:
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
        fonts = self._get_fonts()
        
        y = 4
        
        # Warning text with icons
        warning_full = f"{request.icon} {request.warning_text.upper()} {request.icon}"
        bbox = draw.textbbox((0, 0), warning_full, font=fonts['bold'])
        x = (label_width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), warning_full, fill=1, font=fonts['bold'])
        y += bbox[3] - bbox[1] + 3
        
        # Voltage if provided
        if request.voltage and y + 10 < self.print_height:
            voltage_text = f">>> {request.voltage} <<<"
            bbox = draw.textbbox((0, 0), voltage_text, font=fonts['normal'])
            x = (label_width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), voltage_text, fill=1, font=fonts['normal'])
        
        return img
    
    def create_simple_text_label(self, request: TextLabelRequest) -> Image.Image:
        """Erstellt einfaches einzeiliges Text-Label mit großer Schrift"""
        
        # Dynamische Label-Breite basierend auf Text und Schriftgröße
        estimated_width = len(request.text) * (request.font_size * 0.6)
        label_width = max(180, min(int(estimated_width) + 40, 400))
        
        img = Image.new('1', (label_width, self.print_height), 0)
        draw = ImageDraw.Draw(img)
        
        # Große Schrift laden
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', request.font_size)
        except:
            font = ImageFont.load_default()
        
        # Text zentriert vertikal und horizontal
        bbox = draw.textbbox((0, 0), request.text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Falls Text zu breit, Schrift verkleinern
        if text_width > label_width - 20:
            # Neue Schriftgröße berechnen
            new_font_size = max(8, int(request.font_size * (label_width - 20) / text_width))
            try:
                font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', new_font_size)
            except:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), request.text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        
        # Zentrieren
        x = (label_width - text_width) // 2
        y = (self.print_height - text_height) // 2
        
        # Text zeichnen
        draw.text((x, y), request.text, fill=1, font=font)
        
        return img
    
    def print_label_image(self, image: Image.Image, label_type: str) -> PrintResponse:
        """Print label and create backup"""
        if not self.is_ready:
            raise HTTPException(status_code=503, detail="Printer not ready")
        
        try:
            # Create backup in labels directory
            os.makedirs("/app/labels", exist_ok=True)
            timestamp = datetime.now().strftime("%m%d_%H%M%S")
            filename = f"/app/labels/tech_{label_type}_{timestamp}.png"
            image.save(filename, 'PNG')
            
            # Print via Brother PT
            logger.info(f"🖨️ Printing {label_type} label...")
            self.printer.print_image(image, 50)
            
            return PrintResponse(
                success=True,
                message=f"{label_type.capitalize()} label printed successfully",
                filename=os.path.basename(filename)
            )
            
        except Exception as e:
            logger.error(f"❌ Print error: {e}")
            raise HTTPException(status_code=500, detail=f"Print failed: {e}")

# FastAPI App
app = FastAPI(
    title="Brother PT-E550W Docker Label API",
    description="Professional containerized label printing for electricians & IT technicians",
    version="1.0.0-docker",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for web frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global printer instance
printer_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize printer on startup"""
    global printer_service
    try:
        logger.info("🚀 Starting Brother PT-E550W Docker Service...")
        printer_service = BrotherDockerAPI()
        logger.info("✅ Service startup completed")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")

@app.get("/", tags=["Status"])
async def root():
    """Service overview and status"""
    return {
        "service": "Brother PT-E550W Docker Label API",
        "version": "1.0.0-docker",
        "printer_ready": printer_service.is_ready if printer_service else False,
        "tape_width_mm": printer_service.tape_width if printer_service else None,
        "endpoints": {
            "docs": "/docs - Interactive API Documentation",
            "status": "/status - Printer status",
            "cable": "POST /print/cable - Cable labels for electricians",
            "device": "POST /print/device - Device labels for IT technicians",
            "warning": "POST /print/warning - Safety/warning labels"
        }
    }

@app.get("/status", tags=["Status"])
async def get_printer_status():
    """Get printer status"""
    if not printer_service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return {
        "printer_ready": printer_service.is_ready,
        "tape_width_mm": printer_service.tape_width,
        "print_height_px": printer_service.print_height,
        "container_id": os.environ.get('HOSTNAME', 'unknown'),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/print/cable", response_model=PrintResponse, tags=["Labels"])
async def print_cable_label(request: CableLabelRequest):
    """Print cable label for electricians"""
    if not printer_service:
        raise HTTPException(status_code=503, detail="Printer service unavailable")
    
    image = printer_service.create_cable_label(request)
    return printer_service.print_label_image(image, "cable")

@app.post("/print/device", response_model=PrintResponse, tags=["Labels"])
async def print_device_label(request: DeviceLabelRequest):
    """Print device label for IT technicians"""
    if not printer_service:
        raise HTTPException(status_code=503, detail="Printer service unavailable")
    
    image = printer_service.create_device_label(request)
    return printer_service.print_label_image(image, "device")

@app.post("/print/warning", response_model=PrintResponse, tags=["Labels"])
async def print_warning_label(request: WarningLabelRequest):
    """Print safety/warning label"""
    if not printer_service:
        raise HTTPException(status_code=503, detail="Printer service unavailable")
    
    image = printer_service.create_warning_label(request)
    return printer_service.print_label_image(image, "warning")

@app.post("/print/text", response_model=PrintResponse, tags=["Labels"])
async def print_simple_text_label(request: TextLabelRequest):
    """
    Druckt einfaches einzeiliges Text-Label mit großer Schrift
    
    - **text**: Text für das Label (z.B. "Büro 123", "Server Rack A")  
    - **font_size**: Schriftgröße (Standard: 14, empfohlen: 9-20)
    """
    if not printer_service:
        raise HTTPException(status_code=503, detail="Printer service unavailable")
    
    image = printer_service.create_simple_text_label(request)
    return printer_service.print_label_image(image, "text")

if __name__ == "__main__":
    uvicorn.run(
        "brother_docker_api:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )