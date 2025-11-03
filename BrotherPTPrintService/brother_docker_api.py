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
from typing import Optional, List
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

class BatchTextLabelRequest(BaseModel):
    texts: List[str]  # Liste von Texten für Labels
    font_size: Optional[int] = 14  # Globale Schriftgröße
    separator_margin: Optional[int] = 4   # Pixel zwischen Labels (schmal für Bandersparnis)
    print_individually: Optional[bool] = True  # Einzeln drucken oder als ein Label

# Custom Label Builder Models
class LabelElement(BaseModel):
    type: str  # text, qr, barcode, icon, line, rect
    x: int
    y: int
    id: str
    # Text properties
    text: Optional[str] = None
    fontSize: Optional[int] = None
    fontWeight: Optional[str] = None
    color: Optional[str] = None
    # QR/Barcode properties  
    data: Optional[str] = None
    size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    # Icon properties
    icon: Optional[str] = None
    # Line properties
    x2: Optional[int] = None
    y2: Optional[int] = None
    thickness: Optional[int] = None
    # Rectangle properties
    fillColor: Optional[str] = None
    borderColor: Optional[str] = None
    borderWidth: Optional[int] = None
    # Table properties
    rows: Optional[int] = None
    cols: Optional[int] = None
    tableData: Optional[List[List[str]]] = None

class LabelSettings(BaseModel):
    width: int = 200
    height: int = 62
    margin: int = 5

class CustomLabelRequest(BaseModel):
    elements: List[LabelElement]
    settings: LabelSettings

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
    
    def create_batch_text_labels(self, request: BatchTextLabelRequest) -> List[Image.Image]:
        """Erstellt mehrere Text-Labels mit einheitlicher Konfiguration"""
        
        labels = []
        
        for text in request.texts:
            # Einzelnes Label mit globalen Einstellungen erstellen
            single_request = TextLabelRequest(
                text=text,
                font_size=request.font_size
            )
            label_image = self.create_simple_text_label(single_request)
            labels.append(label_image)
        
        return labels
    
    def print_batch_labels(self, images: List[Image.Image], separator_margin: int, label_type: str) -> PrintResponse:
        """Druckt mehrere Labels als zusammenhängendes Band mit Trennern"""
        
        if not self.is_ready:
            raise HTTPException(status_code=503, detail="Printer not ready")
        
        try:
            # Alle Labels zu einem kontinuierlichen Band zusammenfügen
            combined_image = self.combine_images_to_continuous_band(images, separator_margin)
            
            # PNG-Backup des kombinierten Bandes erstellen
            timestamp = datetime.now().strftime("%m%d_%H%M%S")
            filename = f"/app/labels/batch_{label_type}_combined_{timestamp}.png"
            combined_image.save(filename, 'PNG')
            
            # Gesamtes Band in einem Druckjob drucken
            logger.info(f"🖨️ Printing continuous batch of {len(images)} labels...")
            self.printer.print_image(combined_image, 0)  # Kein extra Margin, da schon eingebaut
            
            return PrintResponse(
                success=True,
                message=f"Continuous batch of {len(images)} {label_type} labels printed successfully (saves label tape!)",
                filename=os.path.basename(filename)
            )
            
        except Exception as e:
            logger.error(f"❌ Batch printing failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Batch printing failed: {str(e)}")
    
    def combine_images_to_continuous_band(self, images: List[Image.Image], separator_margin: int) -> Image.Image:
        """Kombiniert mehrere Label-Bilder zu einem kontinuierlichen Band mit Trennern"""
        
        if not images:
            raise ValueError("No images to combine")
        
        # Höhe ist die maximale Höhe aller Labels (sollte gleich sein für Brother PT)
        max_height = max(img.height for img in images)
        
        # Breite berechnen: alle Labels + dünne 2px Trennstriche zwischen ihnen
        total_width = sum(img.width for img in images) + (2 * (len(images) - 1))
        
        # Brother PT Format für 1-bit Bilder: 0=schwarz (drucken), 1=weiß (kein Druck)  
        # Kombiniertes Bild mit schwarzem Hintergrund wie die einzelnen Labels
        combined = Image.new('1', (total_width, max_height), 0)
        
        # Labels nacheinander einfügen mit dünnen schwarzen Trennstrichen
        x_offset = 0
        separator_line_width = 2  # Dünner schwarzer Trennstrich (2 Pixel breit)
        
        for i, img in enumerate(images):
            # Label einfügen
            combined.paste(img, (x_offset, 0))
            x_offset += img.width
            
            # Dünnen weißen Trennstrich hinzufügen (außer nach dem letzten Label)
            if i < len(images) - 1:
                # 2 Pixel weißer Strich (1 = weiß im 1-bit Modus)
                for x in range(2):
                    for y in range(max_height):
                        combined.putpixel((x_offset + x, y), 1)  # Weißer Trennstrich
                
                x_offset += 2  # Nur die 2 Pixel des Strichs
        
        logger.info(f"📏 Combined {len(images)} labels into {total_width}x{max_height}px continuous band")
        return combined
    
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

    def create_custom_label(self, request: CustomLabelRequest) -> Image.Image:
        """Create custom label from elements"""
        
        settings = request.settings
        width = settings.width
        height = settings.height
        margin = settings.margin
        
        # Create 1-bit image for Brother PT (0=black/print, 1=white/no-print)
        image = Image.new('1', (width, height), 1)  # White background
        draw = ImageDraw.Draw(image)
        
        # Load fonts
        fonts = self._get_fonts()
        
        try:
            # Process each element
            for element in request.elements:
                self._render_element(draw, element, fonts, width, height)
                
        except Exception as e:
            logger.error(f"Error rendering custom label element: {e}")
            raise ValueError(f"Failed to render element: {str(e)}")
        
        return image
    
    def _render_element(self, draw: ImageDraw.Draw, element: LabelElement, fonts: dict, canvas_width: int, canvas_height: int):
        """Render individual element on the canvas"""
        
        x, y = element.x, element.y
        
        if element.type == 'text':
            text = element.text or 'Text'
            font_size = element.fontSize or 12
            font_weight = element.fontWeight or 'normal'
            
            # Select font based on size and weight
            try:
                if font_weight == 'bold':
                    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
                else:
                    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', font_size)
            except:
                font = fonts.get('normal', fonts['normal'])
            
            # Draw text (black=0 for printing)
            draw.text((x, y), text, font=font, fill=0)
            
        elif element.type == 'qr':
            # QR code placeholder - draw a square with QR text
            size = element.size or 30
            draw.rectangle([x, y, x + size, y + size], outline=0, width=2)
            
            # Add QR indicator
            try:
                qr_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', min(size // 4, 8))
                draw.text((x + 2, y + size // 2 - 4), 'QR', font=qr_font, fill=0)
            except:
                draw.text((x + 2, y + size // 2), 'QR', fill=0)
            
        elif element.type == 'barcode':
            # Barcode placeholder - draw lines
            width = element.width or 80
            height = element.height or 20
            
            # Draw barcode-like lines
            bar_width = 2
            num_bars = width // (bar_width * 2)
            
            for i in range(num_bars):
                bar_x = x + i * bar_width * 2
                if i % 2 == 0:  # Alternate bars
                    draw.rectangle([bar_x, y, bar_x + bar_width, y + height], fill=0)
            
        elif element.type == 'icon':
            # Icon/emoji rendering
            icon = element.icon or '⭐'
            size = element.size or 16
            
            try:
                icon_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', size)
                draw.text((x, y), icon, font=icon_font, fill=0)
            except:
                # Fallback: draw a simple shape
                draw.ellipse([x, y, x + size, y + size], outline=0, width=2)
            
        elif element.type == 'line':
            # Draw line
            x2 = element.x2 or (x + 50)
            y2 = element.y2 or y
            thickness = element.thickness or 1
            
            # For thick lines, draw multiple parallel lines
            for i in range(thickness):
                draw.line([x, y + i, x2, y2 + i], fill=0, width=1)
            
        elif element.type == 'rect':
            # Draw rectangle
            width = element.width or 40
            height = element.height or 20
            border_width = element.borderWidth or 1
            fill_color = element.fillColor
            
            # Draw filled rectangle if needed
            if fill_color and fill_color != 'transparent':
                draw.rectangle([x, y, x + width, y + height], fill=0)
            
            # Draw border
            if border_width > 0:
                for i in range(border_width):
                    draw.rectangle([x + i, y + i, x + width - i, y + height - i], outline=0)
                    
        elif element.type == 'table':
            # Simple table rendering
            rows = element.rows or 2
            cols = element.cols or 2
            cell_width = 40
            cell_height = 15
            
            # Draw table grid
            for row in range(rows + 1):
                draw.line([x, y + row * cell_height, x + cols * cell_width, y + row * cell_height], fill=0)
            
            for col in range(cols + 1):
                draw.line([x + col * cell_width, y, x + col * cell_width, y + rows * cell_height], fill=0)
            
            # Add table data if provided
            if element.tableData:
                try:
                    cell_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 8)
                except:
                    cell_font = fonts.get('small', fonts['normal'])
                
                for row_idx, row_data in enumerate(element.tableData[:rows]):
                    for col_idx, cell_data in enumerate(row_data[:cols]):
                        cell_x = x + col_idx * cell_width + 2
                        cell_y = y + row_idx * cell_height + 2
                        draw.text((cell_x, cell_y), str(cell_data), font=cell_font, fill=0)

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
    """API overview and status"""
    return {
        "service": "Brother PT-E550W Docker Label API",
        "version": "1.0.0-docker",
        "pwa": "PWA available at separate service (Port 3000 or via Nginx)",
        "printer_ready": printer_service.is_ready if printer_service else False,
        "tape_width_mm": printer_service.tape_width if printer_service else None,
        "endpoints": {
            "docs": "/docs - Interactive API Documentation",
            "status": "/status - Printer status", 
            "cable": "POST /print/cable - Cable labels for electricians",
            "device": "POST /print/device - Device labels for IT technicians",
            "warning": "POST /print/warning - Safety/warning labels",
            "text": "POST /print/text - Simple text labels with large font",
            "batch": "POST /print/batch - Batch print multiple text labels"
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

@app.post("/print/batch", response_model=PrintResponse, tags=["Labels"])
async def print_batch_text_labels(request: BatchTextLabelRequest):
    """
    Druckt mehrere Text-Labels mit einheitlicher Konfiguration
    
    - **texts**: Liste von Texten (z.B. ["Büro 1", "Büro 2", "Büro 3"])
    - **font_size**: Globale Schriftgröße für alle Labels (Standard: 14)
    - **separator_margin**: Abstand zwischen Labels in Pixel (Standard: 30)
    - **print_individually**: Jedes Label einzeln drucken (Standard: true)
    
    **Beispiele:**
    ```json
    {
      "texts": ["Server Rack A", "Server Rack B", "Server Rack C"],
      "font_size": 16,
      "separator_margin": 50
    }
    ```
    """
    if not printer_service:
        raise HTTPException(status_code=503, detail="Printer service unavailable")
    
    if not request.texts:
        raise HTTPException(status_code=400, detail="Mindestens ein Text erforderlich")
    
    # Labels erstellen
    images = printer_service.create_batch_text_labels(request)
    
    # Batch drucken
    return printer_service.print_batch_labels(images, request.separator_margin, "batch_text")

@app.post("/preview-custom", tags=["Custom Labels"])
async def preview_custom_label(request: CustomLabelRequest):
    """
    Generate preview image for custom label without printing
    
    - **elements**: Array of label elements (text, QR, barcode, etc.)
    - **settings**: Label dimensions and settings
    """
    if not printer_service:
        raise HTTPException(status_code=503, detail="Printer service unavailable")
    
    try:
        image = printer_service.create_custom_label(request)
        
        # Convert to RGB for preview (PNG format)
        if image.mode == '1':  # 1-bit black and white
            rgb_image = Image.new('RGB', image.size)
            rgb_pixels = []
            for pixel in image.getdata():
                # 0 = black pixel (print), 1 = white pixel (no print)
                rgb_pixels.append((255, 255, 255) if pixel else (0, 0, 0))
            rgb_image.putdata(rgb_pixels)
            image = rgb_image
        
        # Save preview to temporary file
        import io
        from fastapi.responses import StreamingResponse
        
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return StreamingResponse(
            io.BytesIO(img_buffer.read()),
            media_type="image/png",
            headers={"Content-Disposition": "inline; filename=preview.png"}
        )
        
    except Exception as e:
        logger.error(f"Custom label preview failed: {e}")
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")

@app.post("/print-custom", response_model=PrintResponse, tags=["Custom Labels"])
async def print_custom_label(request: CustomLabelRequest):
    """
    Print custom label with dynamic elements
    
    - **elements**: Array of label elements with properties:
      - **text**: Text elements with font, size, position
      - **qr**: QR code elements with data and size  
      - **barcode**: Barcode elements with data and dimensions
      - **icon**: Icon/emoji elements with size
      - **line**: Line elements with coordinates and style
      - **rect**: Rectangle elements with dimensions and style
    - **settings**: Label dimensions (width, height, margin)
    
    **Example:**
    ```json
    {
      "elements": [
        {"type": "text", "x": 10, "y": 20, "text": "Custom Label", "fontSize": 12, "id": "text1"},
        {"type": "qr", "x": 10, "y": 35, "data": "https://example.com", "size": 25, "id": "qr1"}
      ],
      "settings": {"width": 200, "height": 62, "margin": 5}
    }
    ```
    """
    if not printer_service:
        raise HTTPException(status_code=503, detail="Printer service unavailable")
    
    if not request.elements:
        raise HTTPException(status_code=400, detail="At least one element required")
    
    try:
        image = printer_service.create_custom_label(request)
        return printer_service.print_label_image(image, "custom")
        
    except Exception as e:
        logger.error(f"Custom label printing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Print failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "brother_docker_api:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )