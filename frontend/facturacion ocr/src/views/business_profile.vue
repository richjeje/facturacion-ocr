<template>
<div class="bg-background-dark text-slate-100 font-display h-screen overflow-hidden flex root-container">
    <Navbar />
    <main class="flex-1 overflow-y-auto pt-10 px-8 pb-20">
        <div class="max-w-6xl w-full mx-auto">

        <div class="flex flex-wrap items-end justify-between gap-4 mb-8">
            <div>
                <h2 class="font-header text-5xl tracking-wide text-white uppercase">
                    {{ user.role === 'negocio' ? 'Perfil de Negocio' : 'Mi Constancia Fiscal' }}
                </h2>
                <p class="text-slate-400 mt-2">
                    <template v-if="user.role === 'negocio'">
                        Gestión de identidad fiscal y validación de perfiles corporativos.
                    </template>
                    <template v-else>
                        Sube tu Constancia de Situación Fiscal (PDF) para actualizar tu información fiscal.
                    </template>
                </p>
            </div>
            <div v-if="user.status === 'pending_approval'" class="flex items-center gap-3 px-4 py-2 bg-charcoal border border-white/5 rounded-lg glow-warning">
                <span class="material-symbols-outlined text-amber-500 text-xl">info</span>
                <p class="text-xs font-medium text-slate-300">Cuenta pendiente de aprobación</p>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <!-- Left Column: Upload CSF -->
            <div class="lg:col-span-1 space-y-6">
                <div class="bg-charcoal p-1 rounded-xl gradient-border overflow-hidden">
                    <div @click="triggerFileUpload"
                        class="drag-zone-gradient border-2 border-dashed border-primary/40 rounded-lg p-8 flex flex-col items-center text-center group cursor-pointer hover:border-primary transition-all csf-upload-area relative">
                        <div
                            class="size-16 rounded-full bg-primary-20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                            <span class="material-symbols-outlined text-primary text-3xl">upload_file</span>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-2">Subir Constancia</h3>
                        <p class="text-[11px] text-slate-400 leading-relaxed font-mono">
                            Formato: PDF con texto seleccionable<br />(máx. 10MB)
                        </p>
                        <button
                            class="mt-6 px-4 py-2 rounded-lg bg-primary-10 border border-primary-30 text-primary text-[10px] font-bold uppercase tracking-wider hover:bg-primary hover:text-white transition-all pointer-events-none">
                            Seleccionar Archivo
                        </button>
                    </div>
                </div>
                <input type="file" id="csf-file-input" accept=".pdf" class="hidden" @change="handleFileUpload">

                <!-- Upload status placeholder -->
                <div v-show="isUploading" class="bg-charcoal p-6 rounded-xl gradient-border">
                    <h4 class="text-sm font-mono text-slate-500 uppercase mb-4 tracking-tighter">Estado de Verificación
                    </h4>
                    <div class="flex items-end justify-between mb-2">
                        <span class="text-2xl font-header tracking-widest">{{ uploadStatusPct }}</span>
                        <span class="text-[10px] font-mono text-slate-400 uppercase">Analizando</span>
                    </div>
                    <div class="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                        <div class="h-full tech-gradient relative transition-all duration-300" :style="{ width: uploadStatusBar }"></div>
                    </div>
                    <p class="mt-4 text-[11px] text-slate-500 italic">{{ uploadStatusMsg }}</p>
                </div>

                <!-- CSFs List Grid -->
                <div class="mt-6">
                    <h4 class="text-sm font-mono text-slate-500 uppercase mb-4 tracking-tighter">Mis Constancias</h4>
                    <div class="flex flex-col gap-3">
                        <div v-if="myCsfs.length === 0" class="text-slate-500 text-xs font-mono">
                            No hay constancias subidas aún.
                        </div>
                        <div v-for="csf in myCsfs" :key="csf.id" class="p-4 bg-charcoal border border-white/5 rounded-lg flex items-center justify-between">
                            <div>
                                <h5 class="text-sm text-white font-bold">{{ csf.filename }}</h5>
                                <p class="text-[10px] text-slate-500 uppercase tracking-widest font-mono mt-1">{{ csf.date }}</p>
                            </div>
                            <span class="material-symbols-outlined text-slate-400 hover:text-white cursor-pointer">visibility</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Column: Profile Data -->
            <div class="lg:col-span-2">
                <div class="bg-charcoal p-8 rounded-xl gradient-border">
                    <div class="flex items-center justify-between mb-8 border-b border-white/5 pb-6">
                        <div class="flex items-center gap-3">
                            <span class="material-symbols-outlined text-secondary">contact_page</span>
                            <h3 class="text-xl font-bold">Datos del Perfil</h3>
                        </div>
                        <span class="text-[10px] font-mono text-slate-500">REF: {{ user.id || 'N/A' }}</span>
                    </div>

                    <form @submit.prevent="saveProfile" class="space-y-6">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div class="space-y-2">
                                <label class="text-[10px] font-mono text-slate-500 uppercase tracking-widest ml-1">Razón
                                    Social</label>
                                <input v-model="user.business_name" :disabled="user.status==='pending_approval'"
                                    class="w-full form-input bg-background-dark border border-white/5 rounded-lg py-3 px-4 font-mono text-sm text-primary transition-all"
                                    type="text" />
                            </div>
                            <div class="space-y-2">
                                <label class="text-[10px] font-mono text-slate-500 uppercase tracking-widest ml-1">RFC</label>
                                <input v-model="user.business_rfc" :disabled="user.status==='pending_approval'"
                                    class="w-full form-input bg-background-dark border border-white/5 rounded-lg py-3 px-4 font-mono text-sm text-primary transition-all"
                                    type="text" />
                            </div>
                            <div class="space-y-2">
                                <label class="text-[10px] font-mono text-slate-500 uppercase tracking-widest ml-1">Representante Legal</label>
                                <input v-model="user.owner_name" :disabled="user.status==='pending_approval'"
                                    class="w-full form-input bg-background-dark border border-white/5 rounded-lg py-3 px-4 font-mono text-sm text-slate-300 transition-all"
                                    type="text" />
                            </div>
                            <div class="space-y-2">
                                <label class="text-[10px] font-mono text-slate-500 uppercase tracking-widest ml-1">Teléfono</label>
                                <input v-model="user.phone" :disabled="user.status==='pending_approval'"
                                    class="w-full form-input bg-background-dark border border-white/5 rounded-lg py-3 px-4 font-mono text-sm text-slate-300 transition-all"
                                    type="tel" />
                            </div>
                            <div class="space-y-2 md:col-span-2">
                                <label class="text-[10px] font-mono text-slate-500 uppercase tracking-widest ml-1">Email de Contacto</label>
                                <input v-model="user.email" :disabled="user.status==='pending_approval'"
                                    class="w-full form-input bg-background-dark border border-white/5 rounded-lg py-3 px-4 font-mono text-sm text-slate-300 transition-all"
                                    type="email" />
                            </div>
                            <div class="space-y-2">
                                <label class="text-[10px] font-mono text-slate-500 uppercase tracking-widest ml-1">Código Postal</label>
                                <input v-model="user.postal_code" :disabled="user.status==='pending_approval'"
                                    class="w-full form-input bg-background-dark border border-white/5 rounded-lg py-3 px-4 font-mono text-sm text-slate-300 transition-all"
                                    type="text" />
                            </div>
                            <div class="space-y-2 md:col-span-2">
                                <label class="text-[10px] font-mono text-slate-500 uppercase tracking-widest ml-1">Dirección Fiscal</label>
                                <textarea v-model="user.address" :disabled="user.status==='pending_approval'"
                                    class="w-full form-input bg-background-dark border border-white/5 rounded-lg py-3 px-4 font-mono text-sm text-slate-300 transition-all resize-none"
                                    rows="3"></textarea>
                            </div>
                        </div>

                        <div v-if="profileMsg" :class="['mt-4 text-sm font-mono p-3 rounded bg-white/5', profileMsgClass]">
                            {{ profileMsg }}
                        </div>

                        <div class="pt-6 flex justify-end">
                            <button :disabled="user.status==='pending_approval'"
                                class="tech-gradient group relative overflow-hidden px-10 py-4 rounded-xl text-white font-bold uppercase tracking-widest text-sm shadow-lg shadow-primary-20 hover:shadow-primary-40 transition-all flex items-center gap-3 disabled:opacity-50"
                                type="submit">
                                <span class="relative z-10">Guardar Cambios</span>
                                <span class="material-symbols-outlined relative z-10">save</span>
                                <div class="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 skew-x-12"></div>
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        </div>
    </main>

    <!-- Modal de Preview y Edición CSF -->
    <div v-if="showPreviewModal" class="csf-preview-modal fixed inset-0 z-[9999] flex items-center justify-center p-4">
        <div class="bg-charcoal border border-white/10 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
            style="box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);">
            <div class="flex justify-between items-center p-6 border-b border-white/5">
                <h3 class="text-xl font-header tracking-wide text-white">Vista Previa - Datos Extraídos</h3>
                <button @click="cancelCSFPreview" class="text-slate-400 hover:text-white transition-colors">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
            <div class="p-6 font-display">
                <div class="mb-6 p-4 bg-primary-10 border border-primary-20 rounded-lg">
                    <div class="flex justify-between text-xs font-mono uppercase tracking-widest text-slate-300 mb-2">
                        <span>Confianza de extracción</span>
                        <strong class="text-primary">{{ extractedConfidence }}%</strong>
                    </div>
                    <div class="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                        <div class="h-full bg-primary" :style="{ width: extractedConfidence + '%' }"></div>
                    </div>
                </div>

                <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-[10px] font-mono text-slate-500 uppercase mb-1">RFC</label>
                            <input type="text" v-model="extractedData.rfc"
                                class="w-full bg-background-dark border border-white/5 rounded py-2 px-3 text-sm text-slate-200 focus-border-primary outline-none">
                            <small class="text-[10px] text-amber-500 mt-1 block">⚠️ Sobreescribirá el actual.</small>
                        </div>
                        <div>
                            <label class="block text-[10px] font-mono text-slate-500 uppercase mb-1">Régimen Fiscal</label>
                            <select v-model="extractedData.regimen"
                                class="w-full bg-background-dark border border-white/5 rounded py-2 px-3 text-sm text-slate-200 focus-border-primary outline-none">
                                <option value="">Seleccionar...</option>
                                <option value="601">601 - General de Ley Personas Morales</option>
                                <option value="603">603 - Personas Morales con Fines no Lucrativos</option>
                                <option value="612">612 - Personas Físicas con Actividades Empresariales</option>
                            </select>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-[10px] font-mono text-slate-500 uppercase mb-1">Nombre/Denominación</label>
                            <input type="text" v-model="extractedData.nombre"
                                class="w-full bg-background-dark border border-white/5 rounded py-2 px-3 text-sm text-slate-200 focus-border-primary outline-none">
                        </div>
                        <div>
                            <label class="block text-[10px] font-mono text-slate-500 uppercase mb-1">Código Postal</label>
                            <input type="text" v-model="extractedData.cp"
                                class="w-full bg-background-dark border border-white/5 rounded py-2 px-3 text-sm text-slate-200 focus-border-primary outline-none">
                        </div>
                    </div>

                    <div>
                        <label class="block text-[10px] font-mono text-slate-500 uppercase mb-1">Dirección Fiscal</label>
                        <textarea v-model="extractedData.direccion" rows="3"
                            class="w-full bg-background-dark border border-white/5 rounded py-2 px-3 text-sm text-slate-200 focus-border-primary outline-none resize-none"></textarea>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-[10px] font-mono text-slate-500 uppercase mb-1">Teléfono</label>
                            <input type="tel" v-model="extractedData.telefono"
                                class="w-full bg-background-dark border border-white/5 rounded py-2 px-3 text-sm text-slate-200 focus-border-primary outline-none">
                        </div>
                        <div>
                            <label class="block text-[10px] font-mono text-slate-500 uppercase mb-1">Email</label>
                            <input type="email" v-model="extractedData.email"
                                class="w-full bg-background-dark border border-white/5 rounded py-2 px-3 text-sm text-slate-200 focus-border-primary outline-none">
                        </div>
                    </div>

                    <div class="mt-4 p-4 bg-background-dark border border-white/5 rounded-lg">
                        <label class="flex items-center gap-3 cursor-pointer">
                            <input type="radio" v-model="extractedData.setAsActive" :value="true"
                                class="bg-charcoal border-white/20 text-primary focus-ring-primary rounded-full">
                            <span class="text-xs font-bold text-slate-300">Establecer como CSF principal para facturación</span>
                        </label>
                    </div>
                </div>
            </div>
            <div class="p-6 border-t border-white/5 flex justify-end gap-3">
                <button @click="cancelCSFPreview"
                    class="px-6 py-2 rounded-lg border border-white/10 text-white text-xs font-bold uppercase tracking-wider hover:bg-white/5 transition-colors">
                    Cancelar
                </button>
                <button @click="applyCSFToProfile"
                    class="px-6 py-2 rounded-lg tech-gradient text-white text-xs font-bold uppercase tracking-wider hover:shadow-lg transition-all">
                    Aplicar y Guardar Perfil
                </button>
            </div>
        </div>
    </div>
</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import Navbar from '../components/navbar.vue';

const user = ref({
    id: '',
    role: '',
    status: '',
    business_name: '',
    business_rfc: '',
    owner_name: '',
    phone: '',
    email: '',
    postal_code: '',
    address: ''
});

const myCsfs = ref<any[]>([]);

const profileMsg = ref('');
const profileMsgClass = ref('');

const isUploading = ref(false);
const uploadStatusPct = ref('0%');
const uploadStatusBar = ref('0%');
const uploadStatusMsg = ref('');

const showPreviewModal = ref(false);
const extractedData = ref<any>({});
const extractedConfidence = ref(95);

const fetchUserProfile = async () => {
    try {
        const token = localStorage.getItem('token');
        if (!token) return;

        const res = await fetch('/api/business/profile', {
            headers: { 'Authorization': 'Bearer ' + token }
        });
        if (res.ok) {
            const data = await res.json();
            user.value = { ...user.value, ...data };
        }
    } catch (e) {
        console.error('Error fetching profile data', e);
    }
};

const saveProfile = async () => {
    profileMsg.value = '';
    profileMsgClass.value = '';

    const params = new URLSearchParams({
        business_name: user.value.business_name || '',
        owner_name: user.value.owner_name || '',
        rfc: user.value.business_rfc || '',
        phone: user.value.phone || '',
        email: user.value.email || '',
        address: user.value.address || '',
        postal_code: user.value.postal_code || ''
    });

    try {
        const res = await fetch('/api/business/profile?' + params.toString(), {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
        });
        const data = await res.json();
        if (res.ok) {
            profileMsg.value = data.message || 'Perfil guardado con éxito';
            profileMsgClass.value = 'text-green-400 border-green-500/20';
        } else {
            profileMsg.value = data.detail || 'Error al guardar el perfil';
            profileMsgClass.value = 'text-red-400 border-red-500/20';
        }
    } catch (e) {
        profileMsg.value = 'Error de conexión';
        profileMsgClass.value = 'text-red-400 border-red-500/20';
    }
};

const triggerFileUpload = () => {
    const el = document.getElementById('csf-file-input') as HTMLInputElement;
    if (el) el.click();
};

const handleFileUpload = (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (!target.files || target.files.length === 0) return;

    isUploading.value = true;
    uploadStatusPct.value = '10%';
    uploadStatusBar.value = '10%';
    uploadStatusMsg.value = 'Analizando constancia...';

    // Simulated parsing delay mimicking OCR
    setTimeout(() => {
        uploadStatusPct.value = '50%';
        uploadStatusBar.value = '50%';
        uploadStatusMsg.value = 'Extrayendo datos...';
    }, 1000);

    setTimeout(() => {
        uploadStatusPct.value = '100%';
        uploadStatusBar.value = '100%';
        uploadStatusMsg.value = 'Análisis completo';
    }, 2000);

    setTimeout(() => {
        isUploading.value = false;
        // Mock extracted data
        extractedData.value = {
            rfc: 'MOCK123456RFC',
            regimen: '601',
            nombre: 'EMPRESA MOCK SA DE CV',
            cp: '12345',
            direccion: 'AV. MOCK 123, COL. CENTRO',
            telefono: '5551234567',
            email: 'contacto@mock.com',
            setAsActive: true
        };
        extractedConfidence.value = 95;
        showPreviewModal.value = true;
        
        // Push mock to csf list
        myCsfs.value.push({
            id: Date.now(),
            filename: target.files?.[0]?.name || 'documento.pdf',
            date: new Date().toLocaleDateString()
        });

        // Reset input
        target.value = '';
    }, 2500);
};

const cancelCSFPreview = () => {
    showPreviewModal.value = false;
};

const applyCSFToProfile = () => {
    user.value.business_rfc = extractedData.value.rfc || user.value.business_rfc;
    user.value.business_name = extractedData.value.nombre || user.value.business_name;
    user.value.postal_code = extractedData.value.cp || user.value.postal_code;
    user.value.address = extractedData.value.direccion || user.value.address;
    user.value.phone = extractedData.value.telefono || user.value.phone;
    user.value.email = extractedData.value.email || user.value.email;
    
    showPreviewModal.value = false;
    saveProfile(); // auto save
};

onMounted(() => {
    fetchUserProfile();
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Mono&family=Sora:wght@300;400;600&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

.root-container {
    background-color: #050508;
}

.bg-background-dark {
    background-color: #050508;
}

.bg-charcoal {
    background-color: #0d0d14;
}

.text-primary {
    color: #7c4dff;
}

.text-secondary {
    color: #4d9fff;
}

.bg-primary {
    background-color: #7c4dff;
}

.bg-primary-10 {
    background-color: rgba(124, 77, 255, 0.1);
}

.bg-primary-20 {
    background-color: rgba(124, 77, 255, 0.2);
}

.border-primary {
    border-color: #7c4dff;
}

.border-primary-20 {
    border-color: rgba(124, 77, 255, 0.2);
}

.border-primary-30 {
    border-color: rgba(124, 77, 255, 0.3);
}

.border-primary-40 {
    border-color: rgba(124, 77, 255, 0.4);
}

.hover\:bg-primary:hover {
    background-color: #7c4dff;
}

.hover\:border-primary:hover {
    border-color: #7c4dff;
}

.hover\:text-primary:hover {
    color: #7c4dff;
}

.shadow-primary-20 {
    box-shadow: 0 10px 15px -3px rgba(124, 77, 255, 0.2), 0 4px 6px -2px rgba(124, 77, 255, 0.1);
}

.hover\:shadow-primary-40:hover {
    box-shadow: 0 10px 15px -3px rgba(124, 77, 255, 0.4), 0 4px 6px -2px rgba(124, 77, 255, 0.2);
}

.focus-border-primary:focus {
    border-color: #7c4dff;
}

.focus-ring-primary:focus {
    --tw-ring-color: #7c4dff;
}

.font-display {
    font-family: 'Sora', sans-serif;
}

.font-header {
    font-family: 'Bebas Neue', cursive;
}

.font-mono {
    font-family: 'Space Mono', monospace;
}

.glow-warning {
    box-shadow: 0 0 15px rgba(255, 159, 67, 0.15);
}

.gradient-border {
    border: 1px solid rgba(255, 255, 255, 0.07);
}

.tech-gradient {
    background: linear-gradient(135deg, #7c4dff 0%, #4d9fff 100%);
}

.drag-zone-gradient {
    background: linear-gradient(135deg, rgba(124, 77, 255, 0.1) 0%, rgba(77, 159, 255, 0.1) 100%);
}

.csf-preview-modal {
    background: rgba(5, 5, 8, 0.85);
    backdrop-filter: blur(4px);
}

.form-input:focus {
    border-color: #7c4dff;
    box-shadow: 0 0 0 1px #7c4dff;
    outline: none;
}
</style>
