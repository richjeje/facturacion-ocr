// frontend/static/js/csf_manager.js
/**
 * Gestor de CSF para perfil de usuario
 * Maneja subida, parsing, preview y aplicación de datos CSF
 */
class CSFManager {
    constructor() {
        this.setupEventListeners();
        this.loadUserCSFs();
        this.csfDataCache = new Map();
        this.currentCSFId = null;
    }
    
    setupEventListeners() {
        const uploadArea = document.getElementById('csf-upload-area');
        const fileInput = document.getElementById('csf-file-input');
        
        if (!uploadArea || !fileInput) {
            console.warn('CSF upload elements not found');
            return;
        }
        
        // Event listeners
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files[0]));
        
        // Prevenir drag por defecto
        document.addEventListener('dragover', (e) => e.preventDefault());
        document.addEventListener('drop', (e) => e.preventDefault());
    }
    
    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        e.currentTarget.style.borderColor = 'var(--mystic-blue)';
        e.currentTarget.style.background = 'rgba(31, 107, 255, 0.1)';
    }
    
    handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const uploadArea = document.getElementById('csf-upload-area');
        uploadArea.style.borderColor = 'var(--border-dim)';
        uploadArea.style.background = 'rgba(255, 255, 255, 0.02)';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleFileSelect(files[0]);
        }
    }
    
    async handleFileSelect(file) {
        if (!file) return;
        
        // Validaciones
        const validation = this.validateCSFFile(file);
        if (!validation.valid) {
            this.showError(validation.error);
            return;
        }
        
        this.showUploadStatus('uploading');
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('/api/profile/upload-csf', {
                method: 'POST',
                body: formData,
                headers: { 
                    'Authorization': 'Bearer ' + localStorage.getItem('token')
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.csfDataCache.set(result.csf_id, result.extracted_data);
                this.showCSFPreview(result.csf_id, result.extracted_data, result.confidence);
                this.showSuccess('✅ CSF procesado. Revisa los datos antes de aplicar.');
            } else {
                this.showError(result.detail || 'Error procesando CSF');
            }
        } catch (error) {
            console.error('Error uploading CSF:', error);
            this.showError('Error de conexión al procesar CSF');
        }
        
        this.hideUploadStatus();
    }
    
    validateCSFFile(file) {
        if (!file) {
            return { valid: false, error: 'No se seleccionó archivo' };
        }
        
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            return { valid: false, error: 'Solo se aceptan archivos PDF' };
        }
        
        if (file.size > 10 * 1024 * 1024) { // 10MB
            return { valid: false, error: 'El archivo excede 10MB' };
        }
        
        return { valid: true };
    }
    
    showUploadStatus(status) {
        const statusDiv = document.getElementById('csf-upload-status');
        if (!statusDiv) return;
        
        statusDiv.style.display = 'block';
        
        // Ocultar todos los estados
        statusDiv.querySelectorAll('div').forEach(div => div.style.display = 'none');
        
        // Mostrar estado específico
        const statusElement = statusDiv.querySelector(`.status-${status}`);
        if (statusElement) {
            statusElement.style.display = 'block';
        }
    }
    
    hideUploadStatus() {
        const statusDiv = document.getElementById('csf-upload-status');
        if (statusDiv) {
            statusDiv.style.display = 'none';
        }
    }
    
    showError(message) {
        const errorSpan = document.getElementById('error-message');
        if (errorSpan) {
            errorSpan.textContent = message;
        }
        this.showUploadStatus('error');
        
        setTimeout(() => this.hideUploadStatus(), 5000);
    }
    
    showSuccess(message) {
        // Mostrar en el status div
        const statusDiv = document.getElementById('csf-upload-status');
        if (statusDiv) {
            const successDiv = statusDiv.querySelector('.status-success');
            if (successDiv) {
                successDiv.querySelector('p').textContent = message;
                statusDiv.style.display = 'block';
            }
        }
        
        setTimeout(() => this.hideUploadStatus(), 3000);
    }
    
    showCSFPreview(csfId, extractedData, confidence) {
        this.currentCSFId = csfId;
        
        // Llenar modal con datos extraídos
        document.getElementById('preview-rfc').value = extractedData.rfc || '';
        document.getElementById('preview-nombre').value = 
            extractedData.nombre_completo || extractedData.denominacion_razon_social || '';
        document.getElementById('preview-cp').value = extractedData.codigo_postal || '';
        document.getElementById('preview-direccion').value = extractedData.direccion_completa || '';
        document.getElementById('preview-telefono').value = extractedData.telefono || '';
        document.getElementById('preview-email').value = extractedData.email || '';
        
        // Configurar selector de régimen fiscal
        this.loadRegimenFiscal(extractedData.regimen_fiscal_key);
        
        // Mostrar confianza
        const confidencePercent = Math.round((confidence || 0.8) * 100);
        document.getElementById('confidence-score').textContent = confidencePercent + '%';
        document.getElementById('confidence-fill').style.width = confidencePercent + '%';
        
        // Color de confianza
        const confidenceFill = document.getElementById('confidence-fill');
        if (confidencePercent >= 80) {
            confidenceFill.style.background = 'var(--success)';
        } else if (confidencePercent >= 60) {
            confidenceFill.style.background = 'var(--mist-purple)';
        } else {
            confidenceFill.style.background = 'var(--error)';
        }
        
        // Mostrar modal
        document.getElementById('csf-preview-modal').style.display = 'flex';
    }
    
    async loadRegimenFiscal(selectedKey) {
        try {
            const response = await fetch('/api/csf/catalogs/regimenes-fiscales', {
                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
            });
            
            const result = await response.json();
            
            if (result.success) {
                const select = document.getElementById('preview-regimen');
                select.innerHTML = '<option value="">Seleccionar...</option>';
                
                for (const [key, description] of Object.entries(result.catalog)) {
                    const option = document.createElement('option');
                    option.value = key;
                    option.textContent = `${key} - ${description}`;
                    if (key === selectedKey) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                }
            }
        } catch (error) {
            console.error('Error loading regimenes fiscales:', error);
        }
    }
    
    async applyCSFToProfile() {
        if (!this.currentCSFId) {
            alert('No hay CSF seleccionado para aplicar');
            return;
        }
        
        try {
            // Recolectar datos editados del modal
            const applyData = {
                rfc: document.getElementById('preview-rfc').value.trim(),
                nombre_completo: document.getElementById('preview-nombre').value.trim(),
                denominacion_razon_social: document.getElementById('preview-nombre').value.trim(),
                codigo_postal: document.getElementById('preview-cp').value.trim(),
                direccion_completa: document.getElementById('preview-direccion').value.trim(),
                telefono: document.getElementById('preview-telefono').value.trim(),
                email: document.getElementById('preview-email').value.trim(),
                regimen_fiscal_key: document.getElementById('preview-regimen').value
            };
            
            const setAsActive = document.getElementById('set-as-active').checked;
            
            const response = await fetch(`/api/profile/apply-csf/${this.currentCSFId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer ' + localStorage.getItem('token')
                },
                body: JSON.stringify({
                    apply_data: applyData,
                    set_as_active: setAsActive,
                    user_notes: 'Aplicación desde preview de CSF'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('✅ Perfil actualizado con datos del CSF');
                this.closeCSFModal();
                this.loadUserCSFs(); // Recargar lista
                this.updateCurrentProfileUI(result.profile_after); // Actualizar perfil visible
            } else {
                alert('Error aplicando CSF: ' + (result.detail || 'Error desconocido'));
            }
        } catch (error) {
            console.error('Error applying CSF to profile:', error);
            alert('Error de conexión al aplicar CSF');
        }
    }
    
    closeCSFModal() {
        document.getElementById('csf-preview-modal').style.display = 'none';
        this.currentCSFId = null;
    }
    
    cancelCSFPreview() {
        this.closeCSFModal();
    }
    
    async loadUserCSFs() {
        try {
            const response = await fetch('/api/profile/csf-list', {
                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.renderCSFCards(result.csf_documents);
            }
        } catch (error) {
            console.error('Error loading CSFs:', error);
        }
    }
    
    renderCSFCards(csfDocuments) {
        const container = document.getElementById('csf-cards-grid');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (csfDocuments.length === 0) {
            container.innerHTML = '<p class="muted">No tienes constancias subidas aún.</p>';
            return;
        }
        
        csfDocuments.forEach(doc => {
            const card = document.createElement('div');
            card.className = `csf-card ${doc.is_active ? 'active' : ''}`;
            
            const confidence = Math.round((doc.confidence || 0) * 100);
            const confidenceColor = confidence >= 80 ? 'var(--success)' : 
                                 confidence >= 60 ? 'var(--mist-purple)' : 'var(--error)';
            
            card.innerHTML = `
                <div class="csf-card-header">
                    <h6>${doc.original_filename}</h6>
                    <span class="confidence-badge" style="background: ${confidenceColor}">
                        Confianza: ${confidence}%
                    </span>
                </div>
                <div class="csf-card-body">
                    <p><strong>RFC:</strong> ${doc.extracted_data?.rfc || 'N/A'}</p>
                    <p><strong>Nombre:</strong> ${doc.extracted_data?.nombre_completo || doc.extracted_data?.denominacion_razon_social || 'N/A'}</p>
                    <p><strong>Fecha:</strong> ${new Date(doc.extraction_date).toLocaleDateString()}</p>
                    ${doc.validation_warnings && doc.validation_warnings.length > 0 ? 
                        `<p class="text-warning"><small>⚠️ ${doc.validation_warnings.length} advertencias</small></p>` : ''
                    }
                </div>
                <div class="csf-card-actions">
                    ${doc.is_active ? 
                        '<span class="active-badge">🏆 Activo</span>' : 
                        `<button onclick="csfManager.setActiveCSF(${doc.id})" class="btn btn-sm btn-outline">Establecer Activo</button>`
                    }
                    <button onclick="csfManager.previewCSF(${doc.id})" class="btn btn-sm">Previsualizar</button>
                    <button onclick="csfManager.deleteCSF(${doc.id}, '${doc.original_filename}')" class="btn btn-sm btn-danger">Eliminar</button>
                </div>
            `;
            
            container.appendChild(card);
        });
    }
    
    previewCSF(csfId) {
        const cachedData = this.csfDataCache.get(csfId);
        if (cachedData) {
            this.showCSFPreview(csfId, cachedData, cachedData.confidence_score || 0.8);
        } else {
            // Cargar desde servidor si no está en cache
            this.loadCSFPreview(csfId);
        }
    }
    
    async loadCSFPreview(csfId) {
        try {
            const response = await fetch(`/api/profile/csf/${csfId}/preview`, {
                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.csfDataCache.set(csfId, result.csf_document.extracted_data);
                this.showCSFPreview(
                    csfId, 
                    result.csf_document.extracted_data, 
                    result.csf_document.confidence
                );
            }
        } catch (error) {
            console.error('Error loading CSF preview:', error);
            alert('Error cargando preview del CSF');
        }
    }
    
    async setActiveCSF(csfId) {
        if (!confirm('¿Establecer esta constancia como principal para facturación?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/profile/set-active-csf/${csfId}`, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('✅ CSF establecido como principal');
                this.loadUserCSFs();
            } else {
                alert('Error: ' + (result.detail || 'Error desconocido'));
            }
        } catch (error) {
            console.error('Error setting active CSF:', error);
            alert('Error de conexión al establecer CSF activo');
        }
    }
    
    async deleteCSF(csfId, filename) {
        if (!confirm(`¿Eliminar la constancia "${filename}"? Esta acción no se puede deshacer.`)) {
            return;
        }
        
        try {
            const response = await fetch(`/api/profile/csf/${csfId}`, {
                method: 'DELETE',
                headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess('✅ CSF eliminado correctamente');
                this.csfDataCache.delete(csfId); // Limpiar cache
                this.loadUserCSFs();
            } else {
                alert('Error: ' + (result.detail || 'Error desconocido'));
            }
        } catch (error) {
            console.error('Error deleting CSF:', error);
            alert('Error de conexión al eliminar CSF');
        }
    }
    
    updateCurrentProfileUI(profileData) {
        // Actualizar campos del formulario principal
        if (profileData.business_name) {
            document.getElementById('p-business-name').value = profileData.business_name;
        }
        if (profileData.business_rfc) {
            document.getElementById('p-rfc').value = profileData.business_rfc;
        }
        if (profileData.owner_name) {
            document.getElementById('p-owner').value = profileData.owner_name;
        }
        if (profileData.phone) {
            document.getElementById('p-phone').value = profileData.phone;
        }
        if (profileData.email) {
            document.getElementById('p-email').value = profileData.email;
        }
        if (profileData.postal_code) {
            document.getElementById('p-zip').value = profileData.postal_code;
        }
        if (profileData.address) {
            document.getElementById('p-address').value = profileData.address;
        }
    }
}

// Funciones globales para onclick en HTML
window.csfManager = new CSFManager();
window.closeCSFModal = () => window.csfManager.closeCSFModal();
window.applyCSFToProfile = () => window.csfManager.applyCSFToProfile();
window.cancelCSFPreview = () => window.csfManager.cancelCSFPreview();