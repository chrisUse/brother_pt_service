// Brother PT Label Generator PWA
// Modern JavaScript with async/await and error handling

class LabelGeneratorApp {
    constructor() {
        // API läuft auf anderer URL/Port als PWA
        this.apiBase = this.getApiBaseUrl();
        this.currentTab = 'text';
        this.isOnline = false;
        
        this.init();
    }

    getApiBaseUrl() {
        // Entwicklung: API auf Port 8000
        // Produktion: API auf Port 8000 oder über Nginx Proxy
        const hostname = window.location.hostname;
        
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
            return `http://${hostname}:8000`;
        }
        
        // In Produktion über Nginx oder Docker Compose
        return `http://${hostname}:8000`;
    }

    async init() {
        console.log('🚀 Brother PT Label Generator PWA gestartet');
        
        // Event Listeners
        this.setupEventListeners();
        
        // Initial status check
        await this.checkPrinterStatus();
        
        // Status regelmäßig prüfen
        setInterval(() => this.checkPrinterStatus(), 30000);
        
        // PWA Install Handler
        this.setupPWAInstall();
        
        // Service Worker registrieren
        this.registerServiceWorker();
    }

    setupEventListeners() {
        // Tab-Switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });

        // Form Submissions
        document.querySelectorAll('.label-form').forEach(form => {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.handleFormSubmit(e.target);
            });
        });

        // Range Input Updates
        this.setupRangeInputs();

        // Batch functionality
        this.setupBatchFeatures();
        
        // Custom label builder
        this.setupCustomLabelBuilder();
    }

    setupCustomLabelBuilder() {
        this.customBuilder = {
            activeTemplate: null,
            elements: [],
            selectedElement: null,
            canvasScale: 1,
            savedTemplates: JSON.parse(localStorage.getItem('customTemplates') || '[]')
        };
        
        this.initializeCustomBuilder();
    }
    
    initializeCustomBuilder() {
        // Template selection
        document.querySelectorAll('.template-card').forEach(card => {
            card.addEventListener('click', () => {
                this.selectTemplate(card.dataset.template);
            });
        });
        
        // Element controls
        document.querySelectorAll('.element-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.addElement(btn.dataset.type);
            });
        });
        
        // Canvas interaction
        const canvas = document.querySelector('.label-canvas');
        if (canvas) {
            canvas.addEventListener('click', this.handleCanvasClick.bind(this));
            canvas.addEventListener('mousemove', this.handleCanvasMove.bind(this));
            canvas.addEventListener('mousedown', this.handleCanvasMouseDown.bind(this));
            canvas.addEventListener('mouseup', this.handleCanvasMouseUp.bind(this));
        }
        
        // Property panel inputs
        document.querySelectorAll('.property-input').forEach(input => {
            input.addEventListener('change', this.updateElementProperty.bind(this));
        });
        
        // Template management buttons
        const saveBtn = document.getElementById('save-template-btn');
        const loadBtn = document.getElementById('load-template-btn');
        const exportBtn = document.getElementById('export-template-btn');
        const importBtn = document.getElementById('import-template-btn');
        const clearBtn = document.getElementById('clear-canvas-btn');
        const previewBtn = document.getElementById('preview-label-btn');
        const printBtn = document.getElementById('print-custom-btn');
        
        if (saveBtn) saveBtn.addEventListener('click', this.saveCurrentTemplate.bind(this));
        if (loadBtn) loadBtn.addEventListener('click', this.loadTemplate.bind(this));
        if (exportBtn) exportBtn.addEventListener('click', this.exportTemplate.bind(this));
        if (importBtn) importBtn.addEventListener('change', this.importTemplate.bind(this));
        if (clearBtn) clearBtn.addEventListener('click', this.clearCanvas.bind(this));
        if (previewBtn) previewBtn.addEventListener('click', this.previewLabel.bind(this));
        if (printBtn) printBtn.addEventListener('click', this.printCustomLabel.bind(this));
        
        // Label settings
        document.querySelectorAll('.label-setting').forEach(input => {
            input.addEventListener('change', this.updateLabelSettings.bind(this));
        });
        
        // Initialize template list
        this.updateTemplateList();
    }
    
    selectTemplate(templateType) {
        // Update active template
        document.querySelectorAll('.template-card').forEach(card => {
            card.classList.remove('active');
        });
        const selectedCard = document.querySelector(`[data-template="${templateType}"]`);
        if (selectedCard) selectedCard.classList.add('active');
        
        this.customBuilder.activeTemplate = templateType;
        this.loadTemplateElements(templateType);
        this.renderCanvas();
    }
    
    loadTemplateElements(templateType) {
        this.customBuilder.elements = [];
        
        switch(templateType) {
            case 'blank':
                // Empty canvas
                break;
            case 'two-line':
                this.customBuilder.elements = [
                    { type: 'text', x: 10, y: 20, text: 'Line 1', fontSize: 12, fontWeight: 'bold', id: 'elem_1' },
                    { type: 'text', x: 10, y: 40, text: 'Line 2', fontSize: 10, fontWeight: 'normal', id: 'elem_2' }
                ];
                break;
            case 'qr-code':
                this.customBuilder.elements = [
                    { type: 'qr', x: 10, y: 10, size: 40, data: 'https://example.com', id: 'elem_1' },
                    { type: 'text', x: 60, y: 30, text: 'QR Label', fontSize: 10, id: 'elem_2' }
                ];
                break;
            case 'barcode':
                this.customBuilder.elements = [
                    { type: 'barcode', x: 10, y: 10, width: 120, height: 30, data: '123456789', id: 'elem_1' },
                    { type: 'text', x: 10, y: 50, text: '123456789', fontSize: 8, id: 'elem_2' }
                ];
                break;
            case 'icon-text':
                this.customBuilder.elements = [
                    { type: 'icon', x: 10, y: 15, icon: '⚠️', size: 20, id: 'elem_1' },
                    { type: 'text', x: 35, y: 30, text: 'Warning', fontSize: 12, fontWeight: 'bold', id: 'elem_2' }
                ];
                break;
            case 'table':
                this.customBuilder.elements = [
                    { type: 'table', x: 10, y: 10, rows: 2, cols: 2, data: [['A1', 'B1'], ['A2', 'B2']], id: 'elem_1' }
                ];
                break;
        }
    }
    
    addElement(elementType) {
        const newElement = {
            type: elementType,
            x: 50,
            y: 25,
            id: 'elem_' + Date.now()
        };
        
        switch(elementType) {
            case 'text':
                Object.assign(newElement, {
                    text: 'Text',
                    fontSize: 12,
                    fontWeight: 'normal',
                    color: '#000000'
                });
                break;
            case 'qr':
                Object.assign(newElement, {
                    data: 'https://example.com',
                    size: 30
                });
                break;
            case 'barcode':
                Object.assign(newElement, {
                    data: '123456789',
                    width: 80,
                    height: 20
                });
                break;
            case 'icon':
                Object.assign(newElement, {
                    icon: '⭐',
                    size: 16
                });
                break;
            case 'line':
                Object.assign(newElement, {
                    x2: 100,
                    y2: 25,
                    thickness: 1,
                    color: '#000000'
                });
                break;
            case 'rect':
                Object.assign(newElement, {
                    width: 40,
                    height: 20,
                    fillColor: 'transparent',
                    borderColor: '#000000',
                    borderWidth: 1
                });
                break;
        }
        
        this.customBuilder.elements.push(newElement);
        this.selectElement(newElement.id);
        this.renderCanvas();
    }
    
    selectElement(elementId) {
        this.customBuilder.selectedElement = elementId;
        this.updatePropertyPanel();
        this.renderCanvas();
    }
    
    updatePropertyPanel() {
        const element = this.customBuilder.elements.find(el => el.id === this.customBuilder.selectedElement);
        if (!element) {
            // Hide all property groups
            document.querySelectorAll('.property-group').forEach(group => {
                group.style.display = 'none';
            });
            return;
        }
        
        // Update basic properties
        const propX = document.getElementById('prop-x');
        const propY = document.getElementById('prop-y');
        if (propX) propX.value = element.x;
        if (propY) propY.value = element.y;
        
        // Show/hide type-specific properties
        document.querySelectorAll('.property-group').forEach(group => {
            group.style.display = 'none';
        });
        
        if (element.type === 'text') {
            const textGroup = document.querySelector('.text-properties');
            if (textGroup) textGroup.style.display = 'block';
            
            const propText = document.getElementById('prop-text');
            const propFontSize = document.getElementById('prop-font-size');
            const propFontWeight = document.getElementById('prop-font-weight');
            const propColor = document.getElementById('prop-color');
            
            if (propText) propText.value = element.text;
            if (propFontSize) propFontSize.value = element.fontSize;
            if (propFontWeight) propFontWeight.value = element.fontWeight;
            if (propColor) propColor.value = element.color;
        }
        
        if (element.type === 'qr') {
            const qrGroup = document.querySelector('.qr-properties');
            if (qrGroup) qrGroup.style.display = 'block';
            
            const propQrData = document.getElementById('prop-qr-data');
            const propQrSize = document.getElementById('prop-qr-size');
            
            if (propQrData) propQrData.value = element.data;
            if (propQrSize) propQrSize.value = element.size;
        }
        
        if (element.type === 'barcode') {
            const barcodeGroup = document.querySelector('.barcode-properties');
            if (barcodeGroup) barcodeGroup.style.display = 'block';
            
            const propBarcodeData = document.getElementById('prop-barcode-data');
            const propBarcodeWidth = document.getElementById('prop-barcode-width');
            const propBarcodeHeight = document.getElementById('prop-barcode-height');
            
            if (propBarcodeData) propBarcodeData.value = element.data;
            if (propBarcodeWidth) propBarcodeWidth.value = element.width;
            if (propBarcodeHeight) propBarcodeHeight.value = element.height;
        }
    }
    
    updateElementProperty(event) {
        const element = this.customBuilder.elements.find(el => el.id === this.customBuilder.selectedElement);
        if (!element) return;
        
        const property = event.target.id.replace('prop-', '').replace(/-/g, '');
        let value = event.target.value;
        
        // Convert numeric properties
        if (['x', 'y', 'fontsize', 'size', 'width', 'height'].includes(property)) {
            value = parseInt(value) || 0;
        }
        
        // Map property names
        const propertyMap = {
            'x': 'x',
            'y': 'y',
            'text': 'text',
            'fontsize': 'fontSize',
            'fontweight': 'fontWeight',
            'color': 'color',
            'qrdata': 'data',
            'qrsize': 'size',
            'barcodedata': 'data',
            'barcodewidth': 'width',
            'barcodeheight': 'height'
        };
        
        const mappedProperty = propertyMap[property] || property;
        element[mappedProperty] = value;
        
        this.renderCanvas();
    }
    
    handleCanvasClick(event) {
        const rect = event.target.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        
        // Find clicked element
        const clickedElement = this.findElementAt(x, y);
        if (clickedElement) {
            this.selectElement(clickedElement.id);
        } else {
            this.customBuilder.selectedElement = null;
            this.updatePropertyPanel();
            this.renderCanvas();
        }
    }
    
    handleCanvasMove(event) {
        // Placeholder for drag functionality
    }
    
    handleCanvasMouseDown(event) {
        // Placeholder for drag start
    }
    
    handleCanvasMouseUp(event) {
        // Placeholder for drag end
    }
    
    findElementAt(x, y) {
        // Simple hit detection - can be improved
        return this.customBuilder.elements.find(element => {
            const margin = 5;
            return x >= element.x - margin && 
                   x <= element.x + (element.width || 50) + margin &&
                   y >= element.y - margin && 
                   y <= element.y + (element.height || 20) + margin;
        });
    }
    
    renderCanvas() {
        const canvas = document.querySelector('.label-canvas');
        if (!canvas) return;
        
        canvas.innerHTML = '';
        
        // Create canvas background
        const background = document.createElement('div');
        background.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: white;
            border: 1px dashed #ccc;
        `;
        canvas.appendChild(background);
        
        // Render elements
        this.customBuilder.elements.forEach(element => {
            const elementDiv = this.createElementDiv(element);
            canvas.appendChild(elementDiv);
        });
    }
    
    createElementDiv(element) {
        const div = document.createElement('div');
        div.dataset.elementId = element.id;
        div.style.position = 'absolute';
        div.style.left = element.x + 'px';
        div.style.top = element.y + 'px';
        div.style.cursor = 'pointer';
        div.style.userSelect = 'none';
        
        if (element.id === this.customBuilder.selectedElement) {
            div.style.outline = '2px solid #007acc';
            div.style.outlineOffset = '1px';
        }
        
        switch(element.type) {
            case 'text':
                div.textContent = element.text;
                div.style.fontSize = element.fontSize + 'px';
                div.style.fontWeight = element.fontWeight;
                div.style.color = element.color;
                div.style.whiteSpace = 'nowrap';
                break;
            case 'qr':
                div.innerHTML = '📱<br>QR';
                div.style.fontSize = Math.min(element.size / 3, 12) + 'px';
                div.style.width = element.size + 'px';
                div.style.height = element.size + 'px';
                div.style.background = '#f0f0f0';
                div.style.display = 'flex';
                div.style.alignItems = 'center';
                div.style.justifyContent = 'center';
                div.style.flexDirection = 'column';
                div.style.border = '1px solid #ccc';
                break;
            case 'barcode':
                div.textContent = '|||||||||||';
                div.style.width = element.width + 'px';
                div.style.height = element.height + 'px';
                div.style.background = '#f0f0f0';
                div.style.display = 'flex';
                div.style.alignItems = 'center';
                div.style.justifyContent = 'center';
                div.style.fontSize = '10px';
                div.style.letterSpacing = '1px';
                div.style.border = '1px solid #ccc';
                break;
            case 'icon':
                div.textContent = element.icon;
                div.style.fontSize = element.size + 'px';
                div.style.lineHeight = '1';
                break;
            case 'line':
                div.style.width = Math.abs(element.x2 - element.x) + 'px';
                div.style.height = element.thickness + 'px';
                div.style.background = element.color;
                break;
            case 'rect':
                div.style.width = element.width + 'px';
                div.style.height = element.height + 'px';
                div.style.background = element.fillColor;
                div.style.border = `${element.borderWidth}px solid ${element.borderColor}`;
                break;
        }
        
        return div;
    }
    
    saveCurrentTemplate() {
        const templateName = prompt('Template Name:');
        if (!templateName) return;
        
        const template = {
            name: templateName,
            elements: JSON.parse(JSON.stringify(this.customBuilder.elements)),
            created: new Date().toISOString()
        };
        
        this.customBuilder.savedTemplates.push(template);
        localStorage.setItem('customTemplates', JSON.stringify(this.customBuilder.savedTemplates));
        
        this.updateTemplateList();
        this.showNotification(`Template "${templateName}" saved`);
    }
    
    updateTemplateList() {
        const select = document.getElementById('template-select');
        if (!select) return;
        
        select.innerHTML = '<option value="">Select Template...</option>';
        
        this.customBuilder.savedTemplates.forEach((template, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = template.name;
            select.appendChild(option);
        });
    }
    
    loadTemplate() {
        const select = document.getElementById('template-select');
        if (!select) return;
        
        const index = select.value;
        if (index === '') return;
        
        const template = this.customBuilder.savedTemplates[index];
        this.customBuilder.elements = JSON.parse(JSON.stringify(template.elements));
        this.renderCanvas();
        this.showNotification(`Template "${template.name}" loaded`);
    }
    
    exportTemplate() {
        if (this.customBuilder.elements.length === 0) {
            this.showNotification('No elements to export', 'error');
            return;
        }
        
        const template = {
            name: prompt('Template Name:') || 'Custom Template',
            elements: this.customBuilder.elements,
            version: '1.0',
            created: new Date().toISOString()
        };
        
        const dataStr = JSON.stringify(template, null, 2);
        const dataBlob = new Blob([dataStr], {type: 'application/json'});
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = template.name.replace(/[^a-z0-9]/gi, '_').toLowerCase() + '.json';
        link.click();
        
        this.showNotification(`Template "${template.name}" exported`);
    }
    
    importTemplate(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const template = JSON.parse(e.target.result);
                if (!template.elements || !Array.isArray(template.elements)) {
                    throw new Error('Invalid template format');
                }
                
                this.customBuilder.elements = template.elements;
                this.renderCanvas();
                this.showNotification(`Template "${template.name || 'Imported'}" loaded`);
            } catch (error) {
                console.error('Template import error:', error);
                this.showNotification('Invalid template file', 'error');
            }
        };
        reader.readAsText(file);
        
        // Reset file input
        event.target.value = '';
    }
    
    clearCanvas() {
        if (this.customBuilder.elements.length === 0) {
            this.showNotification('Canvas is already empty');
            return;
        }
        
        if (confirm('Clear all elements from canvas?')) {
            this.customBuilder.elements = [];
            this.customBuilder.selectedElement = null;
            this.renderCanvas();
            this.updatePropertyPanel();
            this.showNotification('Canvas cleared');
        }
    }
    
    async previewLabel() {
        if (this.customBuilder.elements.length === 0) {
            this.showNotification('No elements to preview', 'error');
            return;
        }
        
        const labelData = this.convertCanvasToLabelData();
        
        try {
            this.showNotification('Generating preview...');
            
            const response = await fetch(`${this.apiBase}/preview-custom`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(labelData)
            });
            
            if (response.ok) {
                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                
                // Show preview in modal
                this.showPreviewModal(url);
                this.showNotification('Preview generated');
            } else {
                throw new Error(`Preview failed: ${response.status}`);
            }
        } catch (error) {
            console.error('Preview failed:', error);
            this.showNotification('Preview failed - check connection', 'error');
        }
    }
    
    showPreviewModal(imageUrl) {
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            cursor: pointer;
        `;
        
        const img = document.createElement('img');
        img.src = imageUrl;
        img.style.cssText = `
            max-width: 90%;
            max-height: 90%;
            background: white;
            padding: 10px;
            border-radius: 5px;
        `;
        
        modal.appendChild(img);
        modal.onclick = () => {
            modal.remove();
            URL.revokeObjectURL(imageUrl);
        };
        
        document.body.appendChild(modal);
    }
    
    async printCustomLabel() {
        if (this.customBuilder.elements.length === 0) {
            this.showNotification('No elements to print', 'error');
            return;
        }
        
        const labelData = this.convertCanvasToLabelData();
        
        try {
            this.showNotification('Printing custom label...');
            
            const response = await fetch(`${this.apiBase}/print-custom`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(labelData)
            });
            
            if (response.ok) {
                this.showNotification('Custom label printed successfully');
            } else {
                const errorText = await response.text();
                throw new Error(`Print failed: ${errorText}`);
            }
        } catch (error) {
            console.error('Print failed:', error);
            this.showNotification('Print failed - check printer connection', 'error');
        }
    }
    
    convertCanvasToLabelData() {
        const labelSettings = {
            width: parseInt(document.getElementById('label-width')?.value || 200),
            height: parseInt(document.getElementById('label-height')?.value || 62),
            margin: parseInt(document.getElementById('label-margin')?.value || 5)
        };
        
        return {
            elements: this.customBuilder.elements,
            settings: labelSettings
        };
    }
    
    updateLabelSettings(event) {
        // Placeholder for label settings changes
        console.log('Label setting changed:', event.target.id, event.target.value);
    }

    setupRangeInputs() {
        const rangeInputs = [
            { input: 'textFontSize', output: 'textFontSizeValue' },
            { input: 'batchFontSize', output: 'batchFontSizeValue' },
            { input: 'batchSeparator', output: 'batchSeparatorValue' }
        ];

        rangeInputs.forEach(({ input, output }) => {
            const inputEl = document.getElementById(input);
            const outputEl = document.getElementById(output);
            
            if (inputEl && outputEl) {
                inputEl.addEventListener('input', () => {
                    outputEl.textContent = `${inputEl.value}px`;
                });
            }
        });
    }

    switchTab(tabName) {
        // Update active tab button
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update active form panel
        document.querySelectorAll('.form-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        document.getElementById(`${tabName}Form`).classList.add('active');

        this.currentTab = tabName;
        console.log(`📋 Switched to ${tabName} tab`);
    }

    async handleFormSubmit(form) {
        const formPanel = form.closest('.form-panel');
        const tabName = formPanel.id.replace('Form', '');
        
        console.log(`📤 Submitting ${tabName} form`);
        
        // Validierung
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        this.showLoading(true);

        try {
            let response;
            
            switch (tabName) {
                case 'text':
                    response = await this.submitTextLabel(form);
                    break;
                case 'cable':
                    response = await this.submitCableLabel(form);
                    break;
                case 'device':
                    response = await this.submitDeviceLabel(form);
                    break;
                case 'warning':
                    response = await this.submitWarningLabel(form);
                    break;
                case 'batch':
                    response = await this.submitBatchLabels(form);
                    break;
                default:
                    throw new Error(`Unbekannter Label-Typ: ${tabName}`);
            }

            this.showResult(response, 'success');
            form.reset();
            this.updateBatchPreview(); // Reset batch preview if needed
            
        } catch (error) {
            console.error(`❌ ${tabName} submission error:`, error);
            this.showResult({
                success: false,
                message: error.message || 'Unbekannter Fehler beim Drucken'
            }, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async submitTextLabel(form) {
        const data = {
            text: form.querySelector('#textContent').value,
            font_size: parseInt(form.querySelector('#textFontSize').value)
        };

        return await this.apiRequest('/print/text', 'POST', data);
    }

    async submitCableLabel(form) {
        const data = {
            cable_type: form.querySelector('#cableType').value
        };
        
        // Optional fields
        const voltage = form.querySelector('#cableVoltage').value;
        if (voltage) data.voltage = voltage;
        
        const destination = form.querySelector('#cableDestination').value;
        if (destination) data.destination = destination;
        
        const colorCode = form.querySelector('#cableColorCode').value;
        if (colorCode) data.color_code = colorCode;

        return await this.apiRequest('/print/cable', 'POST', data);
    }

    async submitDeviceLabel(form) {
        const data = {
            device_name: form.querySelector('#deviceName').value
        };
        
        // Optional fields
        const ip = form.querySelector('#deviceIP').value;
        if (ip) data.ip_address = ip;
        
        const mac = form.querySelector('#deviceMAC').value;
        if (mac) data.mac_address = mac;
        
        const model = form.querySelector('#deviceModel').value;
        if (model) data.model = model;

        return await this.apiRequest('/print/device', 'POST', data);
    }

    async submitWarningLabel(form) {
        const data = {
            warning_text: form.querySelector('#warningText').value,
            icon: form.querySelector('#warningIcon').value
        };
        
        const voltage = form.querySelector('#warningVoltage').value;
        if (voltage) data.voltage = voltage;

        return await this.apiRequest('/print/warning', 'POST', data);
    }

    async submitBatchLabels(form) {
        const textsValue = form.querySelector('#batchTexts').value.trim();
        if (!textsValue) {
            throw new Error('Bitte geben Sie mindestens einen Text ein');
        }
        
        const texts = textsValue.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);
            
        if (texts.length === 0) {
            throw new Error('Keine gültigen Texte gefunden');
        }

        const data = {
            texts: texts,
            font_size: parseInt(form.querySelector('#batchFontSize').value),
            separator_margin: parseInt(form.querySelector('#batchSeparator').value)
        };

        return await this.apiRequest('/print/batch', 'POST', data);
    }

    async apiRequest(endpoint, method = 'GET', data = null) {
        const url = `${this.apiBase}${endpoint}`;
        
        console.log(`🌐 API Request: ${method} ${url}`, data);
        
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        const response = await fetch(url, options);
        const responseData = await response.json();

        if (!response.ok) {
            throw new Error(responseData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        console.log(`✅ API Response:`, responseData);
        return responseData;
    }

    async checkPrinterStatus() {
        try {
            const status = await this.apiRequest('/status');
            this.updateStatusDisplay(status);
            this.isOnline = true;
        } catch (error) {
            console.error('📡 Status check failed:', error);
            this.updateStatusDisplay(null);
            this.isOnline = false;
        }
    }

    updateStatusDisplay(status) {
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        const printerStatus = document.getElementById('printerStatus');

        if (status && status.printer_ready) {
            statusIndicator.textContent = '🟢';
            statusIndicator.className = 'status-indicator online';
            statusText.textContent = 'Online';
            printerStatus.textContent = `Drucker bereit (${status.tape_width_mm}mm Band)`;
        } else if (status) {
            statusIndicator.textContent = '🟡';
            statusIndicator.className = 'status-indicator offline';
            statusText.textContent = 'Drucker nicht bereit';
            printerStatus.textContent = 'Drucker-Initialisierung...';
        } else {
            statusIndicator.textContent = '🔴';
            statusIndicator.className = 'status-indicator offline';
            statusText.textContent = 'Offline';
            printerStatus.textContent = 'Verbindung zum Drucker-Service fehlt';
        }
    }

    setupBatchFeatures() {
        // Batch Text Counter and Preview
        const batchTextarea = document.getElementById('batchTexts');
        if (batchTextarea) {
            batchTextarea.addEventListener('input', () => this.updateBatchPreview());
        }

        // Preset buttons
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.loadPreset(e.target.dataset.preset);
            });
        });

        // Clear batch button
        const clearBtn = document.getElementById('clearBatchBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearBatch());
        }

        // Initial preview
        this.updateBatchPreview();
    }

    updateBatchPreview() {
        const textarea = document.getElementById('batchTexts');
        const counter = document.getElementById('batchCount');
        const tapeUsage = document.getElementById('tapeUsage');
        const previewList = document.getElementById('batchList');
        
        if (!textarea || !counter) return;
        
        const texts = textarea.value.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);
            
        counter.textContent = texts.length;
        
        // Estimate tape usage (rough calculation)
        const avgLabelWidth = 4; // cm average
        const separatorWidth = 0.2; // cm for separator
        const totalWidth = (texts.length * avgLabelWidth) + ((texts.length - 1) * separatorWidth);
        tapeUsage.textContent = `~${totalWidth.toFixed(1)}cm`;
        
        // Update preview list
        if (previewList) {
            previewList.innerHTML = texts.map((text, index) => 
                `<div class="preview-item">
                    <span>${index + 1}. ${text.substring(0, 25)}${text.length > 25 ? '...' : ''}</span>
                    <span>${text.length} Zeichen</span>
                </div>`
            ).join('');
        }
    }

    loadPreset(presetName) {
        const presets = {
            'server-rack': [
                'Server Rack A',
                'Server Rack B', 
                'Server Rack C',
                'Storage Array',
                'Backup Server',
                'Management Switch'
            ],
            'network': [
                'Core Switch',
                'Access Switch 1',
                'Access Switch 2', 
                'WiFi AP North',
                'WiFi AP South',
                'Firewall DMZ',
                'Router WAN'
            ],
            'power': [
                'UPS Main',
                'UPS Backup',
                'PDU Rack A',
                'PDU Rack B',
                'Emergency Power',
                'Generator Input'
            ],
            'office': [
                'Büro 101',
                'Büro 102',
                'Büro 103',
                'Konferenzraum',
                'Serverraum',
                'Empfang',
                'Küche',
                'Lager'
            ]
        };

        const textarea = document.getElementById('batchTexts');
        if (textarea && presets[presetName]) {
            textarea.value = presets[presetName].join('\n');
            this.updateBatchPreview();
            
            // Visual feedback
            this.showNotification(`📋 Preset "${presetName}" geladen (${presets[presetName].length} Labels)`, 'success');
        }
    }

    clearBatch() {
        const textarea = document.getElementById('batchTexts');
        if (textarea) {
            textarea.value = '';
            this.updateBatchPreview();
            this.showNotification('🗑️ Batch-Liste geleert', 'info');
        }
    }

    showNotification(message, type = 'info') {
        // Simple notification - could be enhanced with toast library
        console.log(`${type.toUpperCase()}: ${message}`);
        
        // Update result section temporarily
        const resultsSection = document.getElementById('results');
        const resultContent = document.getElementById('resultContent');
        
        if (resultsSection && resultContent) {
            resultContent.className = `result-content ${type}`;
            resultContent.innerHTML = `<p>${message}</p>`;
            resultsSection.style.display = 'block';
            
            setTimeout(() => {
                resultsSection.style.display = 'none';
            }, 3000);
        }
    }

    showResult(result, type) {
        const resultsSection = document.getElementById('results');
        const resultContent = document.getElementById('resultContent');
        
        resultContent.className = `result-content ${type}`;
        
        if (result.success) {
            resultContent.innerHTML = `
                <h4>✅ ${result.message}</h4>
                ${result.filename ? `<p><strong>Datei:</strong> ${result.filename}</p>` : ''}
                <p><em>Zeitpunkt:</em> ${new Date().toLocaleString('de-DE')}</p>
            `;
        } else {
            resultContent.innerHTML = `
                <h4>❌ Druckfehler</h4>
                <p>${result.message}</p>
                <p><em>Bitte prüfen Sie die Drucker-Verbindung und versuchen Sie es erneut.</em></p>
            `;
        }
        
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth' });
        
        // Auto-hide nach 10 Sekunden bei Erfolg
        if (result.success) {
            setTimeout(() => {
                resultsSection.style.display = 'none';
            }, 10000);
        }
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = show ? 'flex' : 'none';
    }

    // PWA Installation
    setupPWAInstall() {
        let deferredPrompt;
        const installBtn = document.getElementById('installBtn');

        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('💾 PWA install prompt available');
            e.preventDefault();
            deferredPrompt = e;
            installBtn.style.display = 'block';
            installBtn.classList.add('btn-install-pulse');
        });

        installBtn.addEventListener('click', async () => {
            if (!deferredPrompt) return;
            
            installBtn.style.display = 'none';
            deferredPrompt.prompt();
            
            const result = await deferredPrompt.userChoice;
            console.log('🔧 PWA install result:', result);
            deferredPrompt = null;
        });

        window.addEventListener('appinstalled', () => {
            console.log('🎉 PWA successfully installed');
            installBtn.style.display = 'none';
        });
    }

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js');
                console.log('⚙️ Service Worker registered:', registration);
            } catch (error) {
                console.error('❌ Service Worker registration failed:', error);
            }
        }
    }
}

// App starten wenn DOM geladen ist
document.addEventListener('DOMContentLoaded', () => {
    window.labelApp = new LabelGeneratorApp();
});