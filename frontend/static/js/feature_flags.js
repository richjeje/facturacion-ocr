// Agregado al final del archivo frontend/static/js/feature_flags.js

// Funciones para manejo de certificados
window.uploadCertificate = async function() {
    const cerFile = document.getElementById('cer-file').files[0];
    const keyFile = document.getElementById('key-file').files[0];
    const password = document.getElementById('cert-password').value;
    
    if (!cerFile || !keyFile || !password) {
        alert('Por favor, selecciona todos los archivos (CER, KEY) y proporciona la contraseña');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('cer_file', cerFile);
        formData.append('key_file', keyFile);
        formData.append('password', password);
        
        const response = await fetch('/api/cfdi/upload_certificate', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            alert('Certificado subido correctamente');
            console.log('Resultado:', result);
            
            // Opcional: Recargar la lista de certificados
            loadCertificates();
        } else {
            alert('Error al subir certificado: ' + (await response.text()));
        }
    } catch (error) {
        alert('Error de red al subir certificado');
        console.error('Upload error:', error);
    }
};

// Cargar lista de certificados
window.loadCertificates = async function() {
    try {
        const response = await fetch('/api/cfdi/certificates');
        const certificates = await response.json();
        
        const list = document.getElementById('certificates-list');
        list.innerHTML = certificates.map(cert => `
            <div class="card mb-2">
                <div class="flex justify-between items-center">
                    <div>
                        <strong>${cert.certificate_name}</strong>
                        <div class="text-sm text-gray-500">Válido hasta: ${cert.valid_until}</div>
                    </div>
                    <div>
                        <span class="badge ${cert.is_active ? 'badge-success' : 'badge-secondary'}">
                            ${cert.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                    </div>
                </div>
                <div class="text-sm">
                    RFC: ${cert.sat_rfc || 'N/A'}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error cargando certificados:', error);
    }
};

// Llamar al cargar certificados cuando la página se carga
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('certificates-list')) {
        loadCertificates();
    }
});