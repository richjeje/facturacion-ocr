<template>
  <div class="app-container font-display text-slate-100 bg-background-dark selection:bg-primary/30 min-h-screen">
    <div class="flex h-screen overflow-hidden">
      <!-- Sidebar -->
      <navbar />

      <!-- Main Content Area -->
      <main class="flex-1 overflow-y-auto p-8 lg:p-12">
        <header class="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h2 class="font-heading text-6xl tracking-wider text-white">MIS FACTURAS</h2>
            <p class="text-slate-500 mt-2 font-display">Gestiona y consulta el historial de comprobantes fiscales.</p>
          </div>
          <div class="flex items-center gap-4">
            <div class="bg-primary/10 p-4 rounded-xl flex items-center gap-4 border border-primary/20">
              <div class="text-right">
                <p class="text-xs text-slate-500 uppercase font-bold">Total este mes</p>
                <p class="text-xl font-bold text-primary">$45,230.00</p>
              </div>
              <span class="material-symbols-outlined text-primary text-3xl">trending_up</span>
            </div>
          </div>
        </header>

        <!-- Filters & Search -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div class="md:col-span-2 relative group">
            <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <span class="material-symbols-outlined text-slate-500 group-focus-within:text-primary transition-colors">search</span>
            </div>
            <input class="block w-full pl-11 pr-4 py-3 bg-card-dark border border-primary/20 rounded-xl focus:ring-primary focus:border-primary text-white placeholder-slate-500 transition-all outline-none" placeholder="Buscar por RFC o Folio..." type="text"/>
          </div>
          <div class="relative">
            <select class="appearance-none block w-full px-4 py-3 bg-card-dark border border-primary/20 rounded-xl focus:ring-primary focus:border-primary text-white outline-none transition-all">
              <option>Rango de fecha</option>
              <option>Hoy</option>
              <option>Últimos 7 días</option>
              <option>Este mes</option>
            </select>
            <div class="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none">
              <span class="material-symbols-outlined text-slate-500">calendar_month</span>
            </div>
          </div>
          <div class="relative">
            <select class="appearance-none block w-full px-4 py-3 bg-card-dark border border-primary/20 rounded-xl focus:ring-primary focus:border-primary text-white outline-none transition-all">
              <option>Estado: Todos</option>
              <option>Pagada</option>
              <option>Pendiente</option>
              <option>Cancelada</option>
            </select>
            <div class="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none">
              <span class="material-symbols-outlined text-slate-500">filter_list</span>
            </div>
          </div>
        </div>

        <!-- Table Card -->
        <div class="bg-card-dark border border-primary/10 rounded-2xl overflow-hidden glow-border">
          <div class="overflow-x-auto">
            <table class="w-full text-left">
              <thead>
                <tr class="bg-primary/5 text-slate-400">
                  <th class="px-6 py-4 font-display text-xs font-bold uppercase tracking-wider"># Folio</th>
                  <th class="px-6 py-4 font-display text-xs font-bold uppercase tracking-wider">Cliente</th>
                  <th class="px-6 py-4 font-display text-xs font-bold uppercase tracking-wider">Fecha</th>
                  <th class="px-6 py-4 font-display text-xs font-bold uppercase tracking-wider">Monto</th>
                  <th class="px-6 py-4 font-display text-xs font-bold uppercase tracking-wider">Estatus</th>
                  <th class="px-6 py-4 font-display text-xs font-bold uppercase tracking-wider text-right">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-primary/5">
                <tr v-for="invoice in invoices" :key="invoice.folio" class="hover:bg-primary/5 transition-colors group">
                  <td class="px-6 py-5 font-mono text-sm text-secondary">{{ invoice.folio }}</td>
                  <td class="px-6 py-5">
                    <div class="flex flex-col">
                      <span class="font-bold text-sm">{{ invoice.clientName }}</span>
                      <span class="text-xs text-slate-500">{{ invoice.clientRfc }}</span>
                    </div>
                  </td>
                  <td class="px-6 py-5 text-sm text-slate-400">{{ invoice.date }}</td>
                  <td class="px-6 py-5 font-bold">{{ invoice.amount }}</td>
                  <td class="px-6 py-5">
                    <span :class="getStatusClass(invoice.status)">{{ invoice.status }}</span>
                  </td>
                  <td class="px-6 py-5 text-right space-x-2">
                    <button class="text-slate-400 hover:text-primary transition-colors" title="Ver PDF">
                      <span class="material-symbols-outlined text-xl leading-none">picture_as_pdf</span>
                    </button>
                    <button class="text-slate-400 hover:text-secondary transition-colors" title="Descargar XML">
                      <span class="material-symbols-outlined text-xl leading-none">data_object</span>
                    </button>
                    <button class="text-slate-400 hover:text-primary transition-colors" title="Re-enviar">
                      <span class="material-symbols-outlined text-xl leading-none">send</span>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- Pagination -->
          <div class="px-6 py-4 bg-primary/5 border-t border-primary/10 flex items-center justify-between">
            <p class="text-xs text-slate-500 uppercase font-bold tracking-widest">Mostrando 1-4 de 248 facturas</p>
            <div class="flex items-center gap-2">
              <button class="p-2 rounded-lg bg-card-dark border border-primary/20 hover:text-primary transition-colors">
                <span class="material-symbols-outlined">chevron_left</span>
              </button>
              <button class="p-2 rounded-lg bg-primary text-white">1</button>
              <button class="p-2 rounded-lg bg-card-dark border border-primary/20 hover:text-primary transition-colors">2</button>
              <button class="p-2 rounded-lg bg-card-dark border border-primary/20 hover:text-primary transition-colors">3</button>
              <button class="p-2 rounded-lg bg-card-dark border border-primary/20 hover:text-primary transition-colors">
                <span class="material-symbols-outlined">chevron_right</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Cards Bottom -->
        <div class="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="p-6 rounded-2xl bg-card-dark border border-primary/10 glow-border flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-500">
              <span class="material-symbols-outlined">check_circle</span>
            </div>
            <div>
              <p class="text-xs text-slate-500 font-bold uppercase">Pagadas</p>
              <h4 class="text-2xl font-bold">182</h4>
            </div>
          </div>
          <div class="p-6 rounded-2xl bg-card-dark border border-primary/10 glow-border flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-500">
              <span class="material-symbols-outlined">pending_actions</span>
            </div>
            <div>
              <p class="text-xs text-slate-500 font-bold uppercase">Pendientes</p>
              <h4 class="text-2xl font-bold">42</h4>
            </div>
          </div>
          <div class="p-6 rounded-2xl bg-card-dark border border-primary/10 glow-border flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-rose-500/10 flex items-center justify-center text-rose-500">
              <span class="material-symbols-outlined">cancel</span>
            </div>
            <div>
              <p class="text-xs text-slate-500 font-bold uppercase">Canceladas</p>
              <h4 class="text-2xl font-bold">24</h4>
            </div>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import navbar from '../components/navbar.vue';

const invoices = ref([
  { folio: 'F-28492', clientName: 'Tech Solutions SAS', clientRfc: 'TSO120301K32', date: '20 Oct 2023', amount: '$12,450.00', status: 'Pagada' },
  { folio: 'F-28493', clientName: 'Innova Soft S.A.', clientRfc: 'ISO980101M45', date: '22 Oct 2023', amount: '$4,820.50', status: 'Pendiente' },
  { folio: 'F-28494', clientName: 'Marketing Pro', clientRfc: 'MPR150822A12', date: '24 Oct 2023', amount: '$2,100.00', status: 'Cancelada' },
  { folio: 'F-28495', clientName: 'Global Trade Co.', clientRfc: 'GTC101010H11', date: '25 Oct 2023', amount: '$15,900.00', status: 'Pagada' }
]);

const getStatusClass = (status: string) => {
  const baseClasses = 'px-3 py-1 rounded-full text-[10px] font-bold uppercase border';
  if (status === 'Pagada') {
    return `${baseClasses} bg-emerald-500/10 text-emerald-500 border-emerald-500/20`;
  }
  if (status === 'Pendiente') {
    return `${baseClasses} bg-amber-500/10 text-amber-500 border-amber-500/20`;
  }
  if (status === 'Cancelada') {
    return `${baseClasses} bg-rose-500/10 text-rose-500 border-rose-500/20`;
  }
  return baseClasses;
};
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Bebas+Neue&family=Space+Mono&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

.font-display { font-family: 'Space Grotesk', sans-serif; }
.font-heading { font-family: 'Bebas Neue', cursive; }
.font-mono { font-family: 'Space Mono', monospace; }

.bg-background-dark { background-color: #050508; }
.bg-card-dark { background-color: #0d0d14; }
.text-primary { color: #7c4dff; }
.text-secondary { color: #4d9fff; }
.bg-primary { background-color: #7c4dff; }
.bg-primary\/10 { background-color: rgba(124, 77, 255, 0.1); }
.bg-primary\/5 { background-color: rgba(124, 77, 255, 0.05); }
.border-primary\/10 { border-color: rgba(124, 77, 255, 0.1); }
.border-primary\/20 { border-color: rgba(124, 77, 255, 0.2); }
.border-primary\/30 { border-color: rgba(124, 77, 255, 0.3); }

.glow-border { box-shadow: 0 0 15px rgba(124, 77, 255, 0.1); }
.glow-hover:hover { box-shadow: 0 0 20px rgba(124, 77, 255, 0.2); }

.hover\:bg-primary\/5:hover { background-color: rgba(124, 77, 255, 0.05); }
.hover\:text-primary:hover { color: #7c4dff; }
.hover\:text-secondary:hover { color: #4d9fff; }
.focus\:ring-primary:focus { --tw-ring-color: #7c4dff; }
.focus\:border-primary:focus { outline: none; border-color: #7c4dff; box-shadow: 0 0 0 1px #7c4dff; }
.divide-primary\/5 > :not([hidden]) ~ :not([hidden]) { border-color: rgba(124, 77, 255, 0.05); }

/* Scrollbar styles to match the dark theme */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: #050508; 
}
::-webkit-scrollbar-thumb {
  background: rgba(124, 77, 255, 0.2); 
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: rgba(124, 77, 255, 0.4); 
}
</style>
