<template>
  <div class="app-container font-display text-slate-100 bg-[#050508] selection:bg-primary/30">
    <div class="flex min-h-screen">
      <!-- Sidebar -->
      <navbar />
      
      <!-- Main Content -->
      <main class="flex-1 flex flex-col">
        <!-- Header Area -->
        <header class="p-8 pb-4">
          <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <nav class="flex items-center gap-2 text-xs font-technical text-slate-500 mb-2 uppercase tracking-tighter">
                <span>Admin</span>
                <span class="material-symbols-outlined text-[10px]">chevron_right</span>
                <span class="text-primary">Directorio de Clientes</span>
              </nav>
              <h2 class="text-6xl font-heading tracking-tight text-white">MIS CLIENTES</h2>
            </div>
            
            <div class="flex items-center gap-3">
              <button class="btn-gradient glow-hover h-12 px-6 rounded-lg text-white font-bold flex items-center gap-2 transition-all">
                <span class="material-symbols-outlined">person_add</span>
                Nuevo Cliente
              </button>
            </div>
          </div>
          
          <!-- Filters & Search -->
          <div class="mt-8 flex flex-col md:flex-row gap-4 items-center">
            <div class="relative flex-1 w-full">
              <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">search</span>
              <input class="w-full bg-surface-dark border-subtle rounded-lg pl-12 pr-4 py-3 focus:ring-primary focus:border-primary text-sm text-white placeholder:text-slate-600 focus:outline-none transition-all" placeholder="Buscar por nombre, RFC o correo electrónico..." type="text"/>
            </div>
            
            <div class="flex gap-2 w-full md:w-auto">
              <button class="flex items-center justify-center gap-2 px-4 py-3 bg-surface-dark border-subtle rounded-lg text-sm text-slate-400 hover:text-white hover:border-primary/50 transition-all border w-full md:w-auto">
                <span class="material-symbols-outlined text-xl">filter_list</span>
                Filtros
              </button>
              <button class="flex items-center justify-center px-4 py-3 bg-surface-dark border-subtle rounded-lg text-sm text-slate-400 hover:text-white transition-all border w-full md:w-auto">
                <span class="material-symbols-outlined text-xl">download</span>
              </button>
            </div>
          </div>
        </header>

        <!-- Table Area -->
        <section class="p-8 pt-4 flex-1">
          <div class="bg-surface-dark border border-subtle rounded-xl overflow-hidden shadow-2xl">
            <div class="overflow-x-auto">
              <table class="w-full text-left border-collapse">
                <thead>
                  <tr class="bg-white/[0.02] border-b border-subtle">
                    <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Nombre / Razón Social</th>
                    <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">RFC</th>
                    <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Teléfono</th>
                    <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest">Email</th>
                    <th class="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-widest text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-white/[0.05] font-technical text-sm">
                  <tr v-for="client in clients" :key="client.rfc" class="hover:bg-white/[0.03] transition-colors group">
                    <td class="px-6 py-5">
                      <div class="flex items-center gap-3">
                        <div class="size-8 rounded flex items-center justify-center font-bold border" :class="client.color === 'primary' ? 'bg-primary/10 text-primary border-primary/20' : 'bg-accent-blue/10 text-accent-blue border-accent-blue/20'">
                          {{ client.initials }}
                        </div>
                        <span class="text-white font-medium font-display">{{ client.name }}</span>
                      </div>
                    </td>
                    <td class="px-6 py-5 text-slate-400">{{ client.rfc }}</td>
                    <td class="px-6 py-5 text-slate-400">{{ client.phone }}</td>
                    <td class="px-6 py-5 text-slate-400">{{ client.email }}</td>
                    <td class="px-6 py-5 text-right">
                      <button class="px-4 py-1.5 rounded bg-primary/10 border border-primary/30 text-primary font-bold hover:bg-primary/20 transition-all text-xs uppercase tracking-wider">
                        Ver
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Pagination -->
            <div class="p-6 bg-white/[0.02] border-t border-subtle flex items-center justify-between">
              <p class="text-xs text-slate-500 font-technical">Mostrando 1-5 de 24 clientes</p>
              <div class="flex items-center gap-1">
                <button class="size-10 flex items-center justify-center rounded-lg border border-subtle text-slate-500 hover:text-white hover:border-primary transition-all">
                  <span class="material-symbols-outlined text-xl">chevron_left</span>
                </button>
                <button class="size-10 flex items-center justify-center rounded-lg btn-gradient text-white font-bold">1</button>
                <button class="size-10 flex items-center justify-center rounded-lg border border-subtle text-slate-400 hover:text-white transition-all">2</button>
                <button class="size-10 flex items-center justify-center rounded-lg border border-subtle text-slate-400 hover:text-white transition-all">3</button>
                <span class="px-2 text-slate-600">...</span>
                <button class="size-10 flex items-center justify-center rounded-lg border border-subtle text-slate-400 hover:text-white transition-all">5</button>
                <button class="size-10 flex items-center justify-center rounded-lg border border-subtle text-slate-500 hover:text-white hover:border-primary transition-all">
                  <span class="material-symbols-outlined text-xl">chevron_right</span>
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- Bottom Stats -->
        <footer class="px-8 pb-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="p-6 bg-surface-dark border border-subtle rounded-xl flex items-center gap-4">
            <div class="size-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <span class="material-symbols-outlined text-2xl">group</span>
            </div>
            <div>
              <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Total Clientes</p>
              <p class="text-2xl font-bold text-white">24</p>
            </div>
          </div>
          <div class="p-6 bg-surface-dark border border-subtle rounded-xl flex items-center gap-4">
            <div class="size-12 rounded-full bg-accent-blue/10 flex items-center justify-center text-accent-blue">
              <span class="material-symbols-outlined text-2xl">add_chart</span>
            </div>
            <div>
              <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Nuevos (Mes)</p>
              <p class="text-2xl font-bold text-white">+4</p>
            </div>
          </div>
          <div class="p-6 bg-surface-dark border border-subtle rounded-xl flex items-center gap-4">
            <div class="size-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <span class="material-symbols-outlined text-2xl">verified</span>
            </div>
            <div>
              <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">RFCs Verificados</p>
              <p class="text-2xl font-bold text-white">100%</p>
            </div>
          </div>
        </footer>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import navbar from '../components/navbar.vue';

const clients = ref([
  { initials: 'TS', color: 'primary', name: 'TechSolutions S.A. de C.V.', rfc: 'TSO120345K98', phone: '+52 55 1234 5678', email: 'admin@techsolutions.com' },
  { initials: 'ID', color: 'accent-blue', name: 'Innovación Digital', rfc: 'IDI980706A12', phone: '+52 55 8765 4321', email: 'facturas@innovacion.mx' },
  { initials: 'CE', color: 'primary', name: 'Consultoría Élite', rfc: 'CEL150520TR4', phone: '+52 81 4455 6677', email: 'contacto@elite.pro' },
  { initials: 'SG', color: 'accent-blue', name: 'Servicios Globales', rfc: 'SGL101010B23', phone: '+52 33 9988 7766', email: 'billing@global.com' },
  { initials: 'MD', color: 'primary', name: 'Mega Desarrollos', rfc: 'MDE090214L90', phone: '+52 55 2233 4455', email: 'pagos@mega.mx' }
]);
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Bebas+Neue&family=Space+Mono:wght@400;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

/* Applying the custom colors and fonts to generic elements inside this component */
.font-display {
  font-family: 'Space Grotesk', sans-serif;
}
.font-heading {
  font-family: 'Bebas Neue', cursive;
}
.font-technical {
  font-family: 'Space Mono', monospace;
}

.text-primary { color: #7c4dff; }
.bg-primary { background-color: #7c4dff; }
.bg-primary\/30 { background-color: rgba(124, 77, 255, 0.3); }
.bg-primary\/20 { background-color: rgba(124, 77, 255, 0.2); }
.bg-primary\/10 { background-color: rgba(124, 77, 255, 0.1); }
.border-primary { border-color: #7c4dff; }
.border-primary\/20 { border-color: rgba(124, 77, 255, 0.2); }
.border-primary\/30 { border-color: rgba(124, 77, 255, 0.3); }
.border-primary\/50 { border-color: rgba(124, 77, 255, 0.5); }
.hover\:border-primary:hover { border-color: #7c4dff; }
.hover\:border-primary\/50:hover { border-color: rgba(124, 77, 255, 0.5); }
.focus\:ring-primary:focus { --tw-ring-color: #7c4dff; }
.focus\:border-primary:focus { outline: none; border-color: #7c4dff; box-shadow: 0 0 0 1px #7c4dff; }
.shadow-primary\/20 { --tw-shadow-color: rgba(124, 77, 255, 0.2); }

.text-accent-blue { color: #4d9fff; }
.bg-accent-blue\/10 { background-color: rgba(77, 159, 255, 0.1); }
.border-accent-blue\/20 { border-color: rgba(77, 159, 255, 0.2); }

.from-primary { --tw-gradient-from: #7c4dff; --tw-gradient-stops: var(--tw-gradient-from), var(--tw-gradient-to, rgba(124, 77, 255, 0)); }
.to-accent-blue { --tw-gradient-to: #4d9fff; }

.bg-background-light { background-color: #f7f5f8; }
.bg-background-dark { background-color: #050508; }
.bg-surface-dark { background-color: #0d0d14; }

.sidebar-active {
    background: linear-gradient(90deg, #7c4dff 0%, #4d9fff 100%);
}
.btn-gradient {
    background: linear-gradient(135deg, #7c4dff 0%, #4d9fff 100%);
}
.glow-hover:hover {
    box-shadow: 0 0 15px rgba(124, 77, 255, 0.4);
}
.border-subtle {
    border-color: rgba(255, 255, 255, 0.07);
}
</style>
