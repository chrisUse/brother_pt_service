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

        // Batch Text Counter
        const batchTextarea = document.getElementById('batchTexts');
        if (batchTextarea) {
            batchTextarea.addEventListener('input', () => this.updateBatchPreview());
        }
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

    updateBatchPreview() {
        const textarea = document.getElementById('batchTexts');
        const counter = document.getElementById('batchCount');
        
        if (!textarea || !counter) return;
        
        const texts = textarea.value.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);
            
        counter.textContent = texts.length;
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