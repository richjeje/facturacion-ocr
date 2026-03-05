<template>
<div class="bg-[#050508] text-slate-100 font-display min-h-screen py-10 px-6">
  <div class="max-w-6xl w-full mx-auto">
    <div class="mb-10 text-center md:text-left">
      <h2 class="font-heading text-6xl text-white tracking-wide uppercase">Facturar Gastos</h2>
      <p class="text-slate-400 text-lg mt-2">Sube el ticket y el OCR extraerá los datos automáticamente.</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
      <!-- Left Column: Upload Zone -->
      <div class="group relative">
        <div class="gradient-border rounded-xl glow-effect">
          <div @click="triggerUpload" @dragover.prevent @drop.prevent="handleDrop"
            class="bg-[#0d0d14] rounded-[calc(0.75rem-1px)] border-2 border-dashed border-[#7c4dff]/30 hover:border-[#7c4dff]/60 transition-all p-12 flex flex-col items-center justify-center min-h-[400px] cursor-pointer relative overflow-hidden">

            <div v-if="!file" class="flex flex-col items-center">
              <div
                class="size-20 bg-[#7c4dff]/10 rounded-full flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                <span class="material-symbols-outlined text-[#7c4dff] text-5xl">cloud_upload</span>
              </div>
              <h3 class="text-white text-xl font-bold mb-2">Haz clic o arrastra un ticket aquí</h3>
              <p class="text-slate-500 text-sm mb-8">Formatos soportados: JPG, PNG, PDF (Máx. 10MB)</p>
              <button
                class="gradient-bg text-white px-8 py-3 rounded-lg font-bold text-sm tracking-wide hover:opacity-90 transition-opacity shadow-lg shadow-[#7c4dff]/20 uppercase pointer-events-none">
                Seleccionar Archivo
              </button>
            </div>

            <div v-else class="flex flex-col items-center text-center z-10">
              <div class="size-20 bg-[#4d9fff]/20 rounded-full flex items-center justify-center mb-4">
                <span class="material-symbols-outlined text-[#4d9fff] text-4xl">receipt_long</span>
              </div>
              <h3 class="text-white font-bold text-lg mb-1 truncate max-w-xs">{{ file.name }}</h3>
              <p class="text-slate-400 font-mono text-xs mb-6">{{ (file.size / 1024 / 1024).toFixed(2) }} MB</p>
              <button @click.stop="file = null; resetState()"
                class="px-6 py-2 rounded-lg border border-[#1f1f2e] text-slate-400 hover:text-white hover:bg-white/5 transition-all text-xs font-bold uppercase tracking-wider">
                Cambiar Archivo
              </button>
            </div>

            <input type="file" ref="fileInput" @change="handleFileSelected" class="hidden"
              accept="image/jpeg, image/png, application/pdf" />
          </div>
        </div>
      </div>

      <!-- Right Column: Extracted Data -->
      <div class="bg-[#0d0d14] rounded-xl border border-[#1f1f2e] p-8 glow-effect min-h-[400px] flex flex-col">
        <div class="flex items-center justify-between mb-8">
          <div class="flex items-center gap-3">
            <span class="material-symbols-outlined text-[#4d9fff]">analytics</span>
            <h3 class="text-white text-xl font-bold">Datos Extraídos</h3>
          </div>
          <span
            class="px-3 py-1 rounded-full bg-[#4d9fff]/10 text-[#4d9fff] text-[10px] font-bold uppercase tracking-widest border border-[#4d9fff]/20">OCR
            Engine v2.0</span>
        </div>

        <!-- Initial State -->
        <div v-if="state === 'idle'"
          class="flex-1 flex flex-col justify-center items-center text-center py-10 opacity-50">
          <span class="material-symbols-outlined text-6xl text-slate-700 mb-4">document_scanner</span>
          <p class="text-slate-500 font-medium">Esperando documento para analizar...</p>
        </div>

        <!-- Loading State -->
        <div v-else-if="state === 'loading'" class="flex-1 flex flex-col justify-center items-center text-center py-10">
          <div class="mb-6 w-full max-w-xs">
            <div class="flex justify-between mb-2">
              <span class="text-slate-400 text-xs font-medium italic">{{ loadingMessage }}</span>
              <span class="text-[#7c4dff] text-xs font-mono font-bold">{{ progress }}%</span>
            </div>
            <div class="w-full h-1.5 bg-[#1f1f2e] rounded-full overflow-hidden">
              <div
                class="h-full gradient-bg rounded-full shadow-[0_0_10px_rgba(124,77,255,0.5)] transition-all duration-300"
                :style="{ width: progress + '%' }"></div>
            </div>
          </div>

          <div class="grid grid-cols-1 gap-4 w-full">
            <div class="p-4 rounded-lg bg-white/5 border border-[#1f1f2e] animate-pulse">
              <div class="h-4 bg-slate-800 rounded w-1/4 mb-3"></div>
              <div class="h-6 bg-slate-700 rounded w-1/2"></div>
            </div>
            <div class="p-4 rounded-lg bg-white/5 border border-[#1f1f2e] opacity-60">
              <div class="h-4 bg-slate-800 rounded w-1/3 mb-3"></div>
              <div class="h-6 bg-slate-700 rounded w-3/4"></div>
            </div>
          </div>

          <div class="mt-8 flex flex-col items-center gap-2">
            <div class="flex items-center gap-2 text-slate-500">
              <span class="material-symbols-outlined text-sm animate-spin">refresh</span>
              <span class="text-xs uppercase tracking-widest font-bold">Procesando metadatos</span>
            </div>
            <p class="text-[10px] text-slate-600 font-mono">ID: TASK-9821-XPR-00</p>
          </div>
        </div>

        <!-- Done State (Mock Data) -->
        <div v-else-if="state === 'done'" class="flex-1 flex flex-col animate-fadeIn">
          <div class="space-y-4 mb-6">
            <!-- Extracted Field -->
            <div
              class="bg-slate-900/50 border border-slate-800 rounded-xl p-4 transition-all focus-within:border-[#4d9fff]/50">
              <label class="block text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1">Negocio
                Emisor</label>
              <input type="text" v-model="extractedData.emisor"
                class="w-full bg-transparent border-none text-white font-medium p-0 focus:ring-0" />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div
                class="bg-slate-900/50 border border-slate-800 rounded-xl p-4 transition-all focus-within:border-[#4d9fff]/50">
                <label class="block text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1">Fecha</label>
                <input type="text" v-model="extractedData.fecha"
                  class="w-full bg-transparent border-none text-white font-mono p-0 focus:ring-0" />
              </div>
              <div
                class="bg-slate-900/50 border border-slate-800 rounded-xl p-4 transition-all focus-within:border-[#4d9fff]/50">
                <label class="block text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1">Total</label>
                <div class="flex items-center">
                  <span class="text-slate-500 font-mono mr-1">$</span>
                  <input type="text" v-model="extractedData.total"
                    class="w-full bg-transparent border-none text-white font-mono font-bold text-lg p-0 focus:ring-0" />
                </div>
              </div>
            </div>

            <div
              class="bg-slate-900/50 border border-slate-800 rounded-xl p-4 transition-all focus-within:border-[#4d9fff]/50">
              <label class="block text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-1">Concepto
                Principal</label>
              <input type="text" v-model="extractedData.concepto"
                class="w-full bg-transparent border-none text-white p-0 focus:ring-0 text-sm" />
            </div>
          </div>

          <div class="mt-auto pt-6 border-t border-[#1f1f2e] flex justify-end gap-3 rounded-b-xl">
            <button @click="resetState"
              class="px-5 py-2.5 rounded-lg border border-[#1f1f2e] text-slate-400 text-xs font-bold uppercase tracking-wider hover:bg-white/5 transition-colors">
              Rechazar
            </button>
            <button @click="saveExpense"
              class="gradient-bg text-white px-6 py-2.5 rounded-lg text-xs font-bold uppercase tracking-wider hover:opacity-90 shadow-lg shadow-[#7c4dff]/20 transition-all flex items-center gap-2">
              <span>Guardar Factura</span>
              <span class="material-symbols-outlined text-[18px]">check_circle</span>
            </button>
          </div>
        </div>

        <div v-else-if="state === 'saved'" class="flex-1 flex flex-col justify-center items-center text-center py-10">
          <div class="size-20 bg-green-500/20 rounded-full flex items-center justify-center mb-6">
            <span class="material-symbols-outlined text-green-400 text-5xl">task_alt</span>
          </div>
          <h3 class="text-white text-xl font-bold mb-2">¡Gasto Registrado!</h3>
          <p class="text-slate-400 text-sm">El ticket ha sido procesado y guardado correctamente en su base de datos.
          </p>

          <button @click="resetState"
            class="mt-8 px-6 py-2.5 rounded-lg border border-[#1f1f2e] text-slate-300 hover:text-white hover:bg-white/5 transition-all text-sm font-bold uppercase tracking-wider">
            Escanear otro ticket
          </button>
        </div>

        <!-- Footer button states when not done/saved -->
        <div v-if="['idle', 'loading'].includes(state)"
          class="mt-auto pt-6 border-t border-[#1f1f2e] flex justify-end gap-3 mt-6">
          <button disabled
            class="px-5 py-2 rounded-lg border border-[#1f1f2e]/50 text-slate-600 text-xs font-bold uppercase tracking-wider cursor-not-allowed">
            Cancelar
          </button>
          <button disabled
            class="px-5 py-2 rounded-lg bg-slate-800/50 text-slate-600 text-xs font-bold uppercase tracking-wider cursor-not-allowed">
            Guardar Factura
          </button>
        </div>
      </div>
    </div>

    <!-- Summary/Stats Row -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
      <div class="bg-[#0d0d14] border border-[#1f1f2e] p-6 rounded-xl flex items-center gap-4 glow-effect">
        <div class="size-12 rounded-lg bg-[#7c4dff]/10 flex items-center justify-center text-[#7c4dff]">
          <span class="material-symbols-outlined">history</span>
        </div>
        <div>
          <p class="text-slate-500 text-xs uppercase font-bold tracking-widest">Último Gasto</p>
          <p class="text-white text-xl font-mono mt-1">$45.20 <span
              class="text-xs font-display text-slate-400">MXN</span></p>
        </div>
      </div>

      <div class="bg-[#0d0d14] border border-[#1f1f2e] p-6 rounded-xl flex items-center gap-4 glow-effect">
        <div class="size-12 rounded-lg bg-[#4d9fff]/10 flex items-center justify-center text-[#4d9fff]">
          <span class="material-symbols-outlined">assignment_turned_in</span>
        </div>
        <div>
          <p class="text-slate-500 text-xs uppercase font-bold tracking-widest">Procesados hoy</p>
          <p class="text-white text-xl font-mono mt-1">12 <span
              class="text-xs font-display text-slate-400">Tickets</span></p>
        </div>
      </div>

      <div class="bg-[#0d0d14] border border-[#1f1f2e] p-6 rounded-xl flex items-center gap-4 glow-effect">
        <div class="size-12 rounded-lg bg-white/5 flex items-center justify-center text-slate-400">
          <span class="material-symbols-outlined">speed</span>
        </div>
        <div>
          <p class="text-slate-500 text-xs uppercase font-bold tracking-widest">Velocidad OCR</p>
          <p class="text-white text-xl font-mono mt-1">1.2s <span
              class="text-xs font-display text-slate-400">Promedio</span></p>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';

const fileInput = ref<HTMLInputElement | null>(null);
const file = ref<File | null>(null);
const state = ref('idle'); // idle, loading, done, saved
const progress = ref(0);
const loadingMessage = ref('Identificando conceptos...');

const extractedData = reactive({
  emisor: '',
  fecha: '',
  total: '',
  concepto: ''
});

const mockMessages = [
  'Iniciando OCR Engine...',
  'Detectando bordes de la imagen...',
  'Mapeando estructura de texto...',
  'Extrayendo RFC y montos...',
  'Validando formatos de fecha...',
  'Finalizando análisis...'
];

const triggerUpload = () => {
  if (fileInput.value) fileInput.value.click();
};

const handleDrop = (e: DragEvent) => {
  if (e.dataTransfer && e.dataTransfer.files.length > 0) {
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      processFile(droppedFile);
    }
  }
};

const handleFileSelected = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    const selectedFile = target.files[0];
    if (selectedFile) {
      processFile(selectedFile);
    }
  }
};

const processFile = (selectedFile: File) => {
  file.value = selectedFile;
  startOcrSimulation();
};

const resetState = () => {
  file.value = null;
  if (fileInput.value) fileInput.value.value = '';
  state.value = 'idle';
  progress.value = 0;
};

const startOcrSimulation = () => {
  state.value = 'loading';
  progress.value = 0;

  let step = 0;
  const totalSteps = mockMessages.length;

  const interval = setInterval(() => {
    step++;
    progress.value = Math.min(Math.floor((step / (totalSteps * 2)) * 100 * 2), 100);

    if (step % 2 === 0) {
      const msgIdx = Math.min(Math.floor(step / 2), mockMessages.length - 1);
      loadingMessage.value = mockMessages[msgIdx] || '';
    }

    if (progress.value >= 100) {
      clearInterval(interval);
      setTimeout(() => populateMockData(), 500);
    }
  }, 300);
};

const populateMockData = () => {
  extractedData.emisor = 'RESTAURANTE EL BUEN SABOR S.A. DE C.V.';
  const d = new Date();
  extractedData.fecha = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} 14:30`;
  extractedData.total = '1,245.50';
  extractedData.concepto = 'CONSUMO DE ALIMENTOS Y BEBIDAS SEGÚN TICKET 84920';

  state.value = 'done';
};

const saveExpense = () => {
  // Here we would normally make an API call
  state.value = 'saved';
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Grotesk:wght@300..700&family=Space+Mono:ital,wght@0,400;0,700;1,400;1,700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

.font-display {
  font-family: 'Space Grotesk', sans-serif;
}

.font-heading {
  font-family: 'Bebas Neue', cursive;
}

.font-mono {
  font-family: 'Space Mono', monospace;
}

.gradient-border {
  background: linear-gradient(to bottom right, #7c4dff, #4d9fff);
  padding: 1px;
}

.gradient-bg {
  background: linear-gradient(135deg, #7c4dff 0%, #4d9fff 100%);
}

.glow-effect {
  box-shadow: 0 0 20px rgba(124, 77, 255, 0.15);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fadeIn {
  animation: fadeIn 0.4s ease-out forwards;
}
</style>
