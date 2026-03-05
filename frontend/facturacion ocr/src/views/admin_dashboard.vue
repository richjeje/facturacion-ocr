<template>
<div class="admin-dashboard-container bg-background-dark text-high-text h-screen overflow-hidden flex" style="background-color: #050508; color: #f0f0f5;">
    <Navbar />
    <main class="flex-1 overflow-y-auto py-10 px-6">
        <div class="max-w-6xl w-full mx-auto">
        <!-- Breadcrumb & Top Bar -->
        <header class="flex items-center justify-between mb-12">
            <div class="flex items-center gap-2 text-xs uppercase tracking-widest text-muted-text data-font text-[#6b6b80]">
                <router-link to="/admin" class="hover:text-primary transition-colors hover:text-[#7c4dff]">Admin</router-link>
                <span class="material-symbols-outlined text-[10px]">chevron_right</span>
                <span class="text-high-text text-[#f0f0f5]">Dashboard</span>
            </div>
            <router-link to="/dashboard"
                class="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/5 border border-white/10 hover:border-[#7c4dff]/50 transition-all text-sm font-medium text-white no-underline">
                <span class="material-symbols-outlined text-sm">arrow_back</span>
                <span>Volver al Dashboard</span>
            </router-link>
        </header>

        <!-- Page Hero -->
        <section class="mb-12 text-center md:text-left">
            <h2 class="text-7xl title-font text-high-text tracking-tight leading-none mb-2 uppercase text-[#f0f0f5]">Panel de
                Administración</h2>
            <p class="text-muted-text text-lg max-w-2xl text-[#6b6b80]">Gestión de operaciones, validación de identidades fiscales y
                aprobaciones críticas de sistema.</p>
        </section>

        <!-- Main Dashboard Card -->
        <div class="glass-card rounded-2xl p-8 mb-8">
            <div class="flex items-center justify-between mb-8 border-b border-white/5 pb-6">
                <div class="flex items-center gap-3">
                    <div class="w-3 h-3 rounded-full btn-gradient"></div>
                    <h3 class="text-2xl title-font tracking-wide text-high-text text-[#f0f0f5]">Negocios Pendientes de Aprobación</h3>
                </div>
                <div class="flex gap-2">
                    <div
                        class="px-3 py-1 rounded bg-[#7c4dff]/10 border border-[#7c4dff]/20 text-[#7c4dff] text-[10px] font-bold data-font uppercase">
                        {{ pendingUsers.length }} Pendientes</div>
                </div>
            </div>

            <!-- Loading State -->
            <div v-if="loading" class="text-center py-10 text-muted-text text-[#6b6b80]">
                <span class="material-symbols-outlined animate-spin text-4xl mb-2">refresh</span>
                <p>Cargando solicitudes...</p>
            </div>

            <!-- Empty State -->
            <div v-else-if="!pendingUsers || pendingUsers.length === 0" class="text-center py-10 text-muted-text text-[#6b6b80]">
                <span class="material-symbols-outlined text-4xl mb-2 opacity-50">fact_check</span>
                <p>No hay solicitudes pendientes en este momento.</p>
            </div>

            <!-- Pending Table -->
            <div v-else class="overflow-x-auto">
                <table class="w-full text-left border-collapse min-w-[600px]">
                    <thead>
                        <tr class="text-muted-text text-[#6b6b80] text-[10px] uppercase tracking-[0.2em] font-bold data-font">
                            <th class="py-4 px-6 border-b border-white/5">Business Name</th>
                            <th class="py-4 px-6 border-b border-white/5">Username & Email</th>
                            <th class="py-4 px-6 border-b border-white/5">RFC (Tax ID)</th>
                            <th class="py-4 px-6 border-b border-white/5 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-white/5">
                        <tr v-for="u in pendingUsers" :key="u.id" class="group hover:bg-white/[0.02] transition-colors">
                            <td class="py-6 px-6">
                                <div class="flex items-center gap-3">
                                    <div
                                        class="w-8 h-8 rounded bg-white/5 flex items-center justify-center text-[#7c4dff] shrink-0">
                                        <span class="material-symbols-outlined text-sm">corporate_fare</span>
                                    </div>
                                    <span class="font-bold text-high-text text-[#f0f0f5]">{{ u.business_name }}</span>
                                </div>
                            </td>
                            <td class="py-6 px-6">
                                <p class="text-sm text-high-text text-[#f0f0f5]">{{ u.username }}</p>
                                <p class="text-xs text-muted-text text-[#6b6b80] data-font">{{ u.email }}</p>
                            </td>
                            <td class="py-6 px-6 text-sm data-font text-muted-text text-[#6b6b80]">{{ u.business_rfc || 'N/A' }}</td>
                            <td class="py-6 px-6">
                                <div class="flex justify-end gap-3">
                                    <button @click="openApproveModal(u)"
                                        class="px-4 py-2 rounded-lg bg-emerald-500/10 text-emerald-500 text-xs font-bold border border-emerald-500/20 hover:bg-emerald-500 hover:text-white transition-all uppercase tracking-wider">
                                        Aprobar
                                    </button>
                                    <button @click="rejectUser(u.id)"
                                        class="px-4 py-2 rounded-lg bg-rose-500/10 text-rose-500 text-xs font-bold border border-rose-500/20 hover:bg-rose-500 hover:text-white transition-all uppercase tracking-wider">
                                        Rechazar
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Quick Stats Overlay -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
            <div class="glass-card rounded-xl p-6 relative overflow-hidden group">
                <div class="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity text-[#f0f0f5]">
                    <span class="material-symbols-outlined text-6xl">verified</span>
                </div>
                <p class="text-xs uppercase tracking-widest text-[#6b6b80] text-muted-text data-font mb-2">Total Aprobados</p>
                <p class="text-4xl title-font text-high-text text-[#f0f0f5]">1,248</p>
                <div class="mt-4 flex items-center gap-2 text-emerald-500 text-xs font-bold data-font">
                    <span class="material-symbols-outlined text-sm">trending_up</span>
                    <span>+12% esta semana</span>
                </div>
            </div>

            <div class="glass-card rounded-xl p-6 relative overflow-hidden group">
                <div class="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity text-[#f0f0f5]">
                    <span class="material-symbols-outlined text-6xl">pending_actions</span>
                </div>
                <p class="text-xs uppercase tracking-widest text-[#6b6b80] text-muted-text data-font mb-2">SLA de Respuesta</p>
                <p class="text-4xl title-font text-high-text text-[#f0f0f5]">4.2h</p>
                <div class="mt-4 flex items-center gap-2 text-[#7c4dff] text-primary text-xs font-bold data-font">
                    <span class="material-symbols-outlined text-sm">timer</span>
                    <span>Meta: < 6h</span>
                </div>
            </div>

            <div class="glass-card rounded-xl p-6 relative overflow-hidden group">
                <div class="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity text-[#f0f0f5]">
                    <span class="material-symbols-outlined text-6xl">error</span>
                </div>
                <p class="text-xs uppercase tracking-widest text-[#6b6b80] text-muted-text data-font mb-2">Alertas de Fraude</p>
                <p class="text-4xl title-font text-emerald-500">0</p>
                <div class="mt-4 flex items-center gap-2 text-[#6b6b80] text-muted-text text-xs font-bold data-font">
                    <span class="material-symbols-outlined text-sm">check_circle</span>
                    <span>Sistema íntegro</span>
                </div>
            </div>
        </div>
        </div>
    </main>

    <!-- Modal de Aprobación (Vue Controlled) -->
    <div v-if="showModal"
        class="fixed inset-0 z-50 flex items-center justify-center backdrop-blur-sm p-4" style="background-color: rgba(5, 5, 8, 0.8);">
        <div class="glass-card w-full max-w-md rounded-2xl p-8 relative shadow-2xl animate-fadeIn">
            <button @click="closeModal"
                class="absolute top-4 right-4 text-[#6b6b80] text-muted-text hover:text-white transition-colors">
                <span class="material-symbols-outlined">close</span>
            </button>
            <h3 class="text-2xl title-font text-white tracking-wide mb-2 uppercase">Aprobar Negocio</h3>
            <p class="text-sm text-[#6b6b80] text-muted-text mb-6">Asigna una contraseña inicial para el negocio <strong
                    class="text-white">{{ selectedUser?.business_name }}</strong>.</p>

            <form @submit.prevent="submitApprove">
                <div class="mb-6">
                    <label
                        class="block text-[10px] font-bold text-[#6b6b80] text-muted-text uppercase tracking-[0.2em] mb-2 data-font">Contraseña
                        Inicial</label>
                    <input type="password" v-model="initialPassword" required placeholder="••••••••"
                        class="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-3 text-white placeholder:text-[#6b6b80] focus:border-[#7c4dff] focus:ring-0 transition-colors outline-none" />
                </div>

                <div class="flex gap-3">
                    <button type="submit" :disabled="submitting"
                        class="flex-1 btn-gradient py-3 rounded-lg text-white font-bold tracking-wider text-xs uppercase transition-all shadow-lg hover:brightness-110 disabled:opacity-50">
                        {{ submitting ? 'Enviando...' : 'Confirmar Aprobación' }}
                    </button>
                    <button type="button" @click="closeModal"
                        class="px-6 py-3 rounded-lg border border-white/10 text-white font-bold tracking-wider text-xs uppercase hover:bg-white/5 transition-colors">
                        Cancelar
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import Navbar from '../components/navbar.vue';

const pendingUsers = ref<any[]>([]);
const loading = ref(true);
const showModal = ref(false);
const selectedUser = ref<any>(null);
const initialPassword = ref("");
const submitting = ref(false);

const fetchPending = async () => {
    loading.value = true;
    try {
        const token = localStorage.getItem('token');
        if (!token) {
            loading.value = false;
            return;
        }
        const res = await fetch('/api/admin/pending', {
            headers: { 'Authorization': 'Bearer ' + token }
        });

        if (res.ok) {
            const data = await res.json();
            pendingUsers.value = data || [];
        } else {
            console.error('Failed to load pending users');
        }
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
};

const openApproveModal = (user: any) => {
    selectedUser.value = user;
    initialPassword.value = "";
    showModal.value = true;
};

const closeModal = () => {
    showModal.value = false;
    selectedUser.value = null;
    initialPassword.value = "";
};

const submitApprove = async () => {
    if (!selectedUser.value || !initialPassword.value) return;

    submitting.value = true;
    try {
        const params = new URLSearchParams({ password: initialPassword.value });
        const res = await fetch(`/api/admin/approve/${selectedUser.value.id}?${params}`, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
        });

        if (res.ok) {
            alert('Negocio aprobado exitosamente.');
            closeModal();
            fetchPending();
        } else {
            const err = await res.json();
            alert('Error: ' + (err.detail || 'Fallo en aprobación'));
        }
    } catch (e) {
        alert('Error de conexión con el servidor.');
    } finally {
        submitting.value = false;
    }
};

const rejectUser = async (id: number | string) => {
    if (!confirm('¿Estás seguro de rechazar (eliminar) esta solicitud?')) return;

    try {
        const res = await fetch(`/api/admin/reject/${id}`, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + localStorage.getItem('token') }
        });

        if (res.ok) {
            fetchPending();
        } else {
            alert('Error al rechazar usuario.');
        }
    } catch (e) {
        alert('Error de conexión al intentar rechazar.');
    }
};

onMounted(() => {
    fetchPending();
});
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Mono:wght@400;700&family=DM+Sans:wght@400;500;700&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap');

.admin-dashboard-container {
    font-family: 'DM Sans', sans-serif;
    background-color: #050508;
    color: #f0f0f5;
}

.btn-gradient {
    background: linear-gradient(135deg, #7c4dff 0%, #4d9fff 100%);
}

.glass-card {
    background-color: #0d0d14;
    border: 1px solid rgba(255, 255, 255, 0.07);
    transition: all 0.3s ease;
}

.glass-card:hover {
    border-color: rgba(124, 77, 255, 0.3);
    box-shadow: 0 0 20px rgba(124, 77, 255, 0.1);
}

.title-font {
    font-family: 'Bebas Neue', cursive;
}

.data-font {
    font-family: 'Space Mono', monospace;
}

@keyframes fadeIn {
    from {
        opacity: 0;
        transform: scale(0.95);
    }

    to {
        opacity: 1;
        transform: scale(1);
    }
}

.animate-fadeIn {
    animation: fadeIn 0.2s ease-out forwards;
}
</style>
