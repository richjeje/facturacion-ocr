<template>
  <div class="bg-background-dark font-body text-slate-100 h-screen overflow-hidden flex relative">
    <Navbar />
    <!-- Background Decoration Elements -->
    <div class="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/10 rounded-full blur-[120px] pointer-events-none z-0"></div>
    <div class="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent-blue/10 rounded-full blur-[120px] pointer-events-none z-0"></div>

    <main class="flex-1 overflow-y-auto flex justify-center p-6 z-10">
      <div class="w-full max-w-4xl space-y-8 mt-10">
      <!-- Header -->
      <div class="mb-4 text-center md:text-left">
        <h1 class="font-heading text-5xl tracking-wider text-slate-100 mb-2">EMITIR FACTURA</h1>
        <p class="text-slate-400 font-mono text-sm">Complete los datos y registre la constancia de situación fiscal del cliente.</p>
      </div>

      <!-- Form Card -->
      <div class="glass-card rounded-2xl p-6 md:p-10">
        <form id="emitir-factura-form" @submit.prevent="submitForm" class="space-y-6">
          <!-- Row 1 -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="space-y-2">
              <label class="block text-xs font-mono uppercase tracking-widest text-slate-400">Cliente</label>
              <select id="cliente-select" v-model="form.cliente" required class="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 px-4 text-slate-100 focus:outline-none input-focus transition-all duration-300">
                <option value="" disabled>Seleccione un cliente</option>
              </select>
            </div>
            <div class="space-y-2">
              <label class="block text-xs font-mono uppercase tracking-widest text-slate-400">RFC</label>
              <input type="text" id="cliente-rfc" v-model="form.rfc" required class="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 px-4 text-slate-100 placeholder:text-slate-600 focus:outline-none input-focus transition-all duration-300" placeholder="ABC123456XYZ" />
            </div>
            <div class="space-y-2">
              <label class="block text-xs font-mono uppercase tracking-widest text-slate-400">Nombre o Razón Social</label>
              <input type="text" id="cliente-nombre" v-model="form.nombre" required class="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 px-4 text-slate-100 placeholder:text-slate-600 focus:outline-none input-focus transition-all duration-300" placeholder="Empresa S.A. de C.V." />
            </div>
          </div>

          <!-- Domicilio Section -->
          <div id="cliente-domicilio" class="bg-black/20 border border-white/[0.05] rounded-xl p-6 space-y-4">
            <h4 class="font-display font-medium text-primary text-lg flex items-center gap-2">
              <span class="material-symbols-outlined text-xl">location_on</span>
              Domicilio Fiscal
            </h4>

            <div class="space-y-2">
              <input type="text" id="domicilio" v-model="form.domicilio" placeholder="Calle, Colonia, No. Ext, No. Int" required class="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 px-4 text-slate-100 placeholder:text-slate-600 focus:outline-none input-focus transition-all duration-300" />
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <input type="text" id="estado" v-model="form.estado" placeholder="Estado" required class="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 px-4 text-slate-100 placeholder:text-slate-600 focus:outline-none input-focus transition-all duration-300" />
              <input type="text" id="municipio" v-model="form.municipio" placeholder="Municipio" required class="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 px-4 text-slate-100 placeholder:text-slate-600 focus:outline-none input-focus transition-all duration-300" />
              <input type="text" id="postal" v-model="form.postal" placeholder="Código Postal" required class="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 px-4 text-slate-100 placeholder:text-slate-600 focus:outline-none input-focus transition-all duration-300" />
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <input type="text" id="regimen" v-model="form.regimen" placeholder="Régimen Fiscal" required class="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 px-4 text-slate-100 placeholder:text-slate-600 focus:outline-none input-focus transition-all duration-300" />
              <input type="text" id="uso_cfdi" v-model="form.uso_cfdi" placeholder="Uso CFDI" required class="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 px-4 text-slate-100 placeholder:text-slate-600 focus:outline-none input-focus transition-all duration-300" />
            </div>
          </div>

          <!-- Contact & Concept Row -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="block text-xs font-mono uppercase tracking-widest text-slate-400">Teléfono</label>
              <div class="relative">
                <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 text-[20px]">call</span>
                <input type="text" id="telefono" v-model="form.telefono" required class="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 pl-12 pr-4 text-slate-100 placeholder:text-slate-600 focus:outline-none input-focus transition-all duration-300" placeholder="55 1234 5678" />
              </div>
            </div>
            <div class="space-y-2">
              <label class="block text-xs font-mono uppercase tracking-widest text-slate-400">Email</label>
              <div class="relative">
                <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 text-[20px]">mail</span>
                <input type="email" id="email" v-model="form.email" required class="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 pl-12 pr-4 text-slate-100 placeholder:text-slate-600 focus:outline-none input-focus transition-all duration-300" placeholder="contacto@cliente.com" />
              </div>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="md:col-span-2 space-y-2">
              <label class="block text-xs font-mono uppercase tracking-widest text-slate-400">Concepto</label>
              <div class="relative">
                <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 text-[20px]">description</span>
                <input type="text" id="concepto" v-model="form.concepto" required class="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 pl-12 pr-4 text-slate-100 placeholder:text-slate-600 focus:outline-none input-focus transition-all duration-300" placeholder="Descripción del servicio..." />
              </div>
            </div>
            <div class="space-y-2">
              <label class="block text-xs font-mono uppercase tracking-widest text-accent-blue">Total</label>
              <div class="relative">
                <span class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 font-mono text-[20px]">$</span>
                <input type="number" id="total" v-model="form.total" step="0.01" required class="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-3 pl-10 pr-4 text-slate-100 placeholder:text-slate-600 focus:outline-none input-focus transition-all duration-300" placeholder="0.00" />
              </div>
            </div>
          </div>

          <!-- File Upload -->
          <div class="space-y-2 mt-2">
            <div id="pdf-upload-zone" @click="triggerFileInput" class="group border-2 border-dashed border-slate-700 hover:border-accent-blue/50 bg-black/30 hover:bg-accent-blue/5 rounded-xl p-8 text-center cursor-pointer transition-all duration-300">
              <span class="material-symbols-outlined text-4xl text-slate-500 group-hover:text-accent-blue transition-colors mb-2">upload_file</span>
              <p class="font-display text-slate-300 group-hover:text-accent-blue transition-colors text-sm">Adjuntar PDF (Constancia de Situación Fiscal)</p>
              <input type="file" id="pdf-input" ref="fileInput" @change="handleFileUpload" accept="application/pdf" class="hidden" />
              <div id="pdf-selected" class="font-mono text-[11px] text-accent-blue mt-3" v-if="fileName">Adjunto: {{ fileName }}</div>
            </div>
          </div>

          <!-- Submit Button -->
          <div class="pt-6 border-t border-slate-800/50">
            <button type="submit" :disabled="loading" class="gradient-button w-full sm:w-auto px-10 py-4 rounded-xl text-white font-bold tracking-widest text-sm hover:brightness-110 transition-all duration-300 flex items-center justify-center gap-2 float-right disabled:opacity-50">
              <span>{{ loading ? 'PROCESANDO...' : 'EMITIR FACTURA' }}</span>
              <span class="material-symbols-outlined text-[18px]">send</span>
            </button>
            <div class="clear-both"></div>
          </div>
        </form>

        <div id="emitir-factura-result" class="mt-6" v-if="message">
          <div :class="['p-4 rounded-xl border font-mono text-sm', success ? 'bg-green-500/10 border-green-500/30 text-green-400' : 'bg-red-500/10 border-red-500/30 text-red-400']">
            {{ message }}
          </div>
        </div>
      </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import Navbar from '../components/navbar.vue';

const fileInput = ref<HTMLInputElement | null>(null);
const fileName = ref('');
const loading = ref(false);
const message = ref('');
const success = ref(false);

const form = reactive({
  cliente: '',
  rfc: '',
  nombre: '',
  domicilio: '',
  estado: '',
  municipio: '',
  postal: '',
  regimen: '',
  uso_cfdi: '',
  telefono: '',
  email: '',
  concepto: '',
  total: ''
});

const triggerFileInput = () => {
  if (fileInput.value) {
    fileInput.value.click();
  }
};

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) {
    fileName.value = file.name;
  } else {
    fileName.value = '';
  }
};

const submitForm = async () => {
  if (loading.value) return;

  loading.value = true;
  message.value = '';

  try {
    // await new Promise(resolve => setTimeout(resolve, 1000));
    // Integración de API se manejaría aquí

    success.value = true;
    message.value = 'Formulario capturado. Integre la lógica de API aquí.';
  } catch (error) {
    success.value = false;
    message.value = 'Ocurrió un error al emitir la factura.';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Bebas+Neue&family=DM+Sans:wght@400;500;700&family=Space+Mono&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

/* Variables custom portadas de Tailwind config */
.text-primary { color: #9551fb; }
.bg-primary\/10 { background-color: rgba(149, 81, 251, 0.1); }

.text-accent-blue { color: #4d9fff; }
.bg-accent-blue\/10 { background-color: rgba(77, 159, 255, 0.1); }
.bg-accent-blue\/5 { background-color: rgba(77, 159, 255, 0.05); }
.hover\:bg-accent-blue\/5:hover { background-color: rgba(77, 159, 255, 0.05); }
.hover\:border-accent-blue\/50:hover { border-color: rgba(77, 159, 255, 0.5); }
.group:hover .group-hover\:text-accent-blue { color: #4d9fff; }

.bg-background-dark { background-color: #050508; }

.font-display { font-family: 'Space Grotesk', sans-serif; }
.font-heading { font-family: 'Bebas Neue', cursive; }
.font-body { font-family: 'DM Sans', sans-serif; }
.font-mono { font-family: 'Space Mono', monospace; }

.glass-card {
  background: #0d0d14;
  border: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow: 0 0 40px rgba(149, 81, 251, 0.1);
}

.gradient-button {
  background: linear-gradient(135deg, #9551fb 0%, #4d9fff 100%);
  box-shadow: 0 4px 15px rgba(149, 81, 251, 0.4);
}

.input-focus:focus-within {
  border-color: #4d9fff;
  box-shadow: 0 0 0 2px rgba(77, 159, 255, 0.2);
}
</style>
