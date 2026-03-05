<template>
    <aside class="w-64 flex-shrink-0 border-r border-subtle bg-surface-dark flex flex-col sticky top-0 h-screen font-display rounded-r-2xl overflow-hidden">
        <div class="p-6 flex items-center gap-3">
          <div class="size-10 rounded-lg btn-gradient flex items-center justify-center text-white">
            <span class="material-symbols-outlined">center_focus_strong</span>
          </div>
          <h1 class="text-lg font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent-blue">Facturación OCR</h1>
        </div>
        
        <nav class="flex-1 px-4 mt-4 space-y-1">
          <router-link to="/emitir-factura" active-class="sidebar-active !text-white shadow-lg shadow-primary/20" class="flex items-center gap-3 px-3 py-3 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors group">
            <span class="material-symbols-outlined text-xl group-hover:text-primary" :class="{'text-white': $route.path === '/emitir-factura'}">description</span>
            <span class="text-sm font-medium" :class="{'font-bold': $route.path === '/emitir-factura'}">Emitir Factura</span>
          </router-link>
          
          <router-link to="/admin" active-class="sidebar-active !text-white shadow-lg shadow-primary/20" class="flex items-center gap-3 px-3 py-3 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors group">
            <span class="material-symbols-outlined text-xl group-hover:text-primary" :class="{'text-white': $route.path === '/admin'}">visibility</span>
            <span class="text-sm font-medium" :class="{'font-bold': $route.path === '/admin'}">Facturación OCR</span>
          </router-link>
          
          <router-link to="/mis-facturas" active-class="sidebar-active !text-white shadow-lg shadow-primary/20" class="flex items-center gap-3 px-3 py-3 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors group">
            <span class="material-symbols-outlined text-xl group-hover:text-primary" :class="{'text-white': $route.path === '/mis-facturas'}">business_center</span>
            <span class="text-sm font-medium" :class="{'font-bold': $route.path === '/mis-facturas'}">Facturación del Negocio</span>
          </router-link>
          
          <router-link to="/mis-clientes" active-class="sidebar-active !text-white shadow-lg shadow-primary/20" class="flex items-center gap-3 px-3 py-3 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors group">
            <span class="material-symbols-outlined text-xl group-hover:text-primary" :class="{'text-white': $route.path === '/mis-clientes'}">group</span>
            <span class="text-sm font-medium" :class="{'font-bold': $route.path === '/mis-clientes'}">Clientes</span>
          </router-link>
          
          <div class="pt-4 pb-2">
            <p class="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest">Sistema</p>
          </div>
          
          <router-link to="/business-profile" active-class="sidebar-active !text-white shadow-lg shadow-primary/20" class="flex items-center gap-3 px-3 py-3 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors group">
            <span class="material-symbols-outlined text-xl group-hover:text-primary" :class="{'text-white': $route.path === '/business-profile'}">settings</span>
            <span class="text-sm font-medium" :class="{'font-bold': $route.path === '/business-profile'}">Configuración</span>
          </router-link>
          
          <router-link to="/config-profile" active-class="sidebar-active !text-white shadow-lg shadow-primary/20" class="flex items-center gap-3 px-3 py-3 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors group">
            <span class="material-symbols-outlined text-xl group-hover:text-primary" :class="{'text-white': $route.path === '/config-profile'}">account_circle</span>
            <span class="text-sm font-medium" :class="{'font-bold': $route.path === '/config-profile'}">Perfil</span>
          </router-link>
        </nav>
        
        <div class="p-4 border-t border-subtle">
          <div class="flex items-center gap-3 p-2 rounded-xl bg-white/5 border border-white/5">
            <div class="size-8 rounded-full bg-primary/20 flex items-center justify-center border border-primary/30 overflow-hidden">
              <img alt="Admin Profile" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBlWhGJvtOcYlA3d08pSQB4jG3TvUshbAAfHh1qstvJl5seSX1pFi-WSo3UFgKS7WfRsAxj3Wo5QP60fH5Rk-nF98929kshrtj143WS4BiONK9vHt_KVoBLaIh-QXWyLlzYW8Ox5yJPXoMd2T8z2bMcJzKX_ZexEJZIVmRwgO64Amv-qlH7gJwClRC0rVfAG-4uMFTks6T69qic8crX4FEHlt8nxRsbzXNNnnmAeLJmam10KyH3ApbEYHrrOJCPOhNTS-nB3wKv8O8"/>
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-xs font-bold truncate text-white">Admin Elite</p>
              <p class="text-[10px] text-slate-500 truncate">Premium Plan</p>
            </div>
            <span class="material-symbols-outlined text-slate-500 text-sm">unfold_more</span>
          </div>
        </div>
      </aside>
</template>

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