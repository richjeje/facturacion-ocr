<template>
<div class="font-sora h-screen overflow-hidden bg-background-dark text-slate-100 flex">
  <Navbar />
  <main class="flex-1 overflow-y-auto p-8">
    <div class="max-w-5xl mx-auto space-y-8">

    <!-- Header Section -->
    <header class="flex flex-col md:flex-row md:items-end justify-between gap-6">
      <div>
        <h2 class="font-bebas text-6xl tracking-tight text-white uppercase leading-none">Configuración</h2>
        <p class="text-slate-400 mt-2 font-display">Gestiona los parámetros de identidad y perfiles fiscales de tu organización.</p>
      </div>
      <div class="flex items-center gap-4">
        <button form="perfil-form" type="submit" class="gradient-btn px-8 py-3 rounded-lg font-semibold text-sm text-white glow-hover transition-all flex items-center gap-2 outline-none">
          <span class="material-symbols-outlined text-sm">save</span>
          Guardar Cambios
        </button>
      </div>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">

      <!-- Left Column: Profile & Docs -->
      <div class="lg:col-span-1 space-y-6">
        <!-- Profile Card -->
        <section class="bg-surface-dark border border-white/5 p-6 rounded-xl">
          <h3 class="text-white font-semibold mb-6 flex items-center gap-2">
            <span class="material-symbols-outlined text-primary">account_circle</span>
            Foto de Perfil
          </h3>
          <div class="flex flex-col items-center">
            <div class="relative group">
              <div class="size-32 rounded-full border-2 border-primary/50 neon-border p-1">
                <template v-if="user.profile_photo">
                  <div class="w-full h-full rounded-full bg-cover bg-center" :style="{ backgroundImage: 'url(' + user.profile_photo + ')' }"></div>
                </template>
                <template v-else>
                  <div class="w-full h-full rounded-full bg-background-dark flex items-center justify-center text-4xl text-slate-600 font-bebas">
                    {{ (user.business_name || user.username || 'U')[0]?.toUpperCase() || 'U' }}
                  </div>
                </template>
              </div>
              <button class="absolute bottom-0 right-0 bg-primary p-2 rounded-full text-white shadow-lg hover:scale-110 transition-transform">
                <span class="material-symbols-outlined text-sm">edit</span>
              </button>
            </div>
            <div class="mt-4 text-center">
              <p class="text-white font-bold text-lg">{{ user.business_name || user.username }}</p>
              <p class="text-slate-500 font-mono text-xs uppercase tracking-widest mt-1">
                RFC: <span class="text-slate-400">{{ user.business_rfc || 'NO ASIGNADO' }}</span>
              </p>
            </div>
          </div>
        </section>

        <!-- Documents Card -->
        <section class="bg-surface-dark border border-white/5 p-6 rounded-xl">
          <h3 class="text-white font-semibold mb-6 flex items-center gap-2">
            <span class="material-symbols-outlined text-primary">picture_as_pdf</span>
            Constancia Fiscal
          </h3>
          <div class="space-y-4">
            <input type="file" ref="fileInput" accept="application/pdf" class="hidden" @change="handleFileChange">
            <div @click="triggerFileInput" class="p-4 border-2 border-dashed border-white/10 rounded-lg flex flex-col items-center justify-center gap-2 hover:border-primary/50 transition-colors cursor-pointer group">
              <span class="material-symbols-outlined text-3xl text-slate-500 group-hover:text-primary transition-colors">upload_file</span>
              <p class="text-sm text-slate-400">Seleccionar archivo PDF</p>
            </div>
            <button @click="triggerFileInput" class="w-full py-3 rounded-lg border border-primary/30 text-primary font-semibold text-sm hover:bg-primary/10 transition-all flex items-center justify-center gap-2 focus:outline-none">
              <span class="material-symbols-outlined text-sm">add</span>
              Agregar Nuevo PDF
            </button>
          </div>
        </section>
      </div>

      <!-- Right Column: Business Data Form -->
      <div class="lg:col-span-2">
        <section class="bg-surface-dark border border-white/5 p-8 rounded-xl h-full flex flex-col">
          <h3 class="text-white font-semibold mb-8 flex items-center gap-2">
            <span class="material-symbols-outlined text-primary">business</span>
            Datos de la Empresa
          </h3>

          <form id="perfil-form" @submit.prevent="saveProfile" class="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1">
            <div class="md:col-span-2 space-y-2">
              <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Nombre / Razón Social</label>
              <input id="perf-name" required v-model="user.business_name" class="w-full bg-background-dark border-white/10 rounded-lg text-white font-mono focus:border-primary focus:ring-1 focus:ring-primary py-3 transition-all" type="text" />
            </div>
            <div class="space-y-2">
              <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider">RFC</label>
              <input id="perf-rfc" required v-model="user.business_rfc" class="w-full bg-background-dark border-white/10 rounded-lg text-white font-mono focus:border-primary focus:ring-1 focus:ring-primary py-3 transition-all" type="text" />
            </div>
            <div class="space-y-2">
              <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Código Postal</label>
              <input id="perf-postal" required v-model="user.postal_code" class="w-full bg-background-dark border-white/10 rounded-lg text-white font-mono focus:border-primary focus:ring-1 focus:ring-primary py-3 transition-all" type="text" />
            </div>
            <div class="space-y-2">
              <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Email Corporativo</label>
              <input id="perf-email" required v-model="user.email" class="w-full bg-background-dark border-white/10 rounded-lg text-white font-mono focus:border-primary focus:ring-1 focus:ring-primary py-3 transition-all" type="email" />
            </div>
            <div class="space-y-2">
              <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Teléfono de Contacto</label>
              <input id="perf-phone" required v-model="user.phone" class="w-full bg-background-dark border-white/10 rounded-lg text-white font-mono focus:border-primary focus:ring-1 focus:ring-primary py-3 transition-all" type="text" />
            </div>
            <div class="md:col-span-2 space-y-2">
              <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Domicilio Fiscal</label>
              <textarea id="perf-address" required v-model="user.address" class="w-full bg-background-dark border-white/10 rounded-lg text-white font-mono focus:border-primary focus:ring-1 focus:ring-primary py-3 transition-all resize-none" rows="3"></textarea>
            </div>
          </form>

          <template v-if="user.status === 'approved'">
            <div class="mt-8 flex items-center justify-between p-4 bg-primary/5 rounded-lg border border-primary/20">
              <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-primary">verified</span>
                <div>
                  <p class="text-sm font-semibold text-white">Estado de Validación</p>
                  <p class="text-xs text-slate-400">Datos validados y aprobados por el administrador.</p>
                </div>
              </div>
              <span class="text-xs font-mono bg-emerald-500/20 text-emerald-400 px-3 py-1 rounded-full border border-emerald-500/30">ACTIVO</span>
            </div>
          </template>
          <template v-else-if="user.status === 'pending_approval'">
            <div class="mt-8 flex items-center justify-between p-4 bg-amber-500/5 rounded-lg border border-amber-500/20">
              <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-amber-500">pending_actions</span>
                <div>
                  <p class="text-sm font-semibold text-amber-500">Revisión Pendiente</p>
                  <p class="text-xs text-slate-400">El registro requiere aprobación antes de facturar.</p>
                </div>
              </div>
              <span class="text-xs font-mono bg-amber-500/20 text-amber-400 px-3 py-1 rounded-full border border-amber-500/30">PENDIENTE</span>
            </div>
          </template>

        </section>
      </div>

    </div>

    <!-- Danger Zone / Secondary Actions -->
    <div class="flex flex-col sm:flex-row items-center justify-between pt-8 pb-4 border-t border-white/5 gap-4">
      <div class="text-slate-500 text-xs font-mono order-2 sm:order-1 flex gap-4">
        <router-link to="/dashboard" class="hover:text-slate-300 transition-colors">← Volver al Dashbaord</router-link>
        <router-link to="/logout" class="text-rose-400 hover:text-rose-300 transition-colors">Cerrar Sesión</router-link>
      </div>
      <div class="flex gap-4 order-1 sm:order-2">
        <button type="button" @click="resetForm" class="px-6 py-2 rounded-lg text-slate-400 hover:text-white text-sm font-medium transition-colors outline-none">
          Descartar Cambios
        </button>
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

const user = reactive({
  username: 'Usuario',
  business_name: '',
  business_rfc: '',
  postal_code: '',
  email: '',
  phone: '',
  address: '',
  profile_photo: '',
  status: 'pending_approval' // 'approved' or 'pending_approval'
});

const initialUser = { ...user };

const triggerFileInput = () => {
  if (fileInput.value) fileInput.value.click();
};

const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target && target.files && target.files.length > 0) {
    console.log("Archivo PDF seleccionado:", target.files[0]?.name);
    // Add logic to process the selected PDF
  }
};

const saveProfile = () => {
  console.log("Guardando Perfil:", { ...user });
  // API call logic
};

const resetForm = () => {
  Object.assign(user, initialUser);
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Sora:wght@300;400;600;700&family=Space+Mono:wght@400;700&family=Bebas+Neue&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

.sidebar-active {
  background: linear-gradient(90deg, rgba(149, 81, 251, 0.15) 0%, rgba(59, 130, 246, 0) 100%);
  border-left: 4px solid #9551fb;
}

.gradient-btn {
  background: linear-gradient(135deg, #9551fb 0%, #3b82f6 100%);
}

.glow-hover:hover {
  box-shadow: 0 0 15px rgba(149, 81, 251, 0.4);
}

.neon-border {
  box-shadow: 0 0 10px rgba(149, 81, 251, 0.5), inset 0 0 5px rgba(149, 81, 251, 0.3);
}

.font-sora {
  font-family: 'Sora', sans-serif;
}

.font-display {
  font-family: 'Space Grotesk', sans-serif;
}

.font-mono {
  font-family: 'Space Mono', monospace;
}

.font-bebas {
  font-family: 'Bebas Neue', cursive;
}

/* Base custom colors - tailwind values */
:deep(.text-primary) { color: #9551fb; }
:deep(.bg-primary) { background-color: #9551fb; }
:deep(.border-primary) { border-color: #9551fb; }
:deep(.ring-primary) { --tw-ring-color: #9551fb; }

:deep(.text-secondary) { color: #3b82f6; }
:deep(.bg-secondary) { background-color: #3b82f6; }
:deep(.border-secondary) { border-color: #3b82f6; }

:deep(.bg-background-light) { background-color: #f7f5f8; }
:deep(.bg-background-dark) { background-color: #050508; }
:deep(.bg-surface-dark) { background-color: #0d0d14; }

/* Focus util colors */
:global(input:focus), :global(textarea:focus) {
  border-color: #9551fb !important;
  --tw-ring-color: #9551fb !important;
}

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer utilities {
  .text-primary { color: #9551fb; }
  .bg-primary { background-color: #9551fb; }
  .border-primary { border-color: #9551fb; }
  .bg-background-dark { background-color: #050508; }
  .bg-surface-dark { background-color: #0d0d14; }
}

</style>
