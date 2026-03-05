<template>
  <div class="bg-background-dark font-body text-slate-100 min-h-screen flex flex-col items-center justify-center p-4">
    <div class="w-full flex justify-center">
      <!-- Background Decoration Elements -->
      <div class="fixed top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/10 rounded-full blur-[120px] pointer-events-none"></div>
      <div class="fixed bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent-blue/10 rounded-full blur-[120px] pointer-events-none"></div>

      <div class="w-full max-w-[440px] z-10">
        <!-- Logo Section -->
        <div class="flex flex-col items-center mb-10">
          <div class="bg-primary/20 p-3 rounded-xl mb-4 border border-primary/30">
            <svg class="w-10 h-10 text-primary" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
              <path d="M44 11.2727C44 14.0109 39.8386 16.3957 33.69 17.6364C39.8386 18.877 44 21.2618 44 24C44 26.7382 39.8386 29.123 33.69 30.3636C39.8386 31.6043 44 33.9891 44 36.7273C44 40.7439 35.0457 44 24 44C12.9543 44 4 40.7439 4 36.7273C4 33.9891 8.16144 31.6043 14.31 30.3636C8.16144 29.123 4 26.7382 4 24C4 21.2618 8.16144 18.877 14.31 17.6364C8.16144 16.3957 4 14.0109 4 11.2727C4 7.25611 12.9543 4 24 4C35.0457 4 44 7.25611 44 11.2727Z" fill="currentColor"></path>
            </svg>
          </div>
          <h2 class="font-display font-bold text-xl tracking-tight text-slate-100">Facturación <span class="text-primary">OCR</span></h2>
        </div>

        <!-- Login Card -->
        <div class="glass-card rounded-2xl p-8 md:p-10 w-full">
          <h1 class="font-heading text-5xl text-center mb-8 tracking-wider text-slate-100">INICIAR SESIÓN</h1>
          <form @submit.prevent="doLogin" class="space-y-6">

            <div v-if="errorMsg" class="bg-red-500/20 border border-red-500/50 text-red-200 p-3 rounded-xl text-sm text-center">
              {{ errorMsg }}
            </div>

            <!-- User Input -->
            <div class="space-y-2">
              <label class="block text-left text-sm font-medium text-slate-300 mb-1">Usuario</label>
              <div class="relative">
                <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 text-[20px]">person</span>
                <input v-model="username" required class="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-4 pl-12 pr-4 text-slate-100 placeholder:text-slate-600 focus:outline-none input-focus transition-all duration-300" placeholder="Ingrese su usuario" type="text" />
              </div>
            </div>

            <!-- Password Input -->
            <div class="space-y-2">
              <div class="flex justify-between items-center mb-1">
                <label class="block text-left text-sm font-medium text-slate-300">Contraseña</label>
                <a class="text-xs font-mono text-slate-500 hover:text-primary transition-colors uppercase tracking-tighter" href="#">¿Olvidó su clave?</a>
              </div>
              <div class="relative">
                <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 text-[20px]">lock</span>
                <input v-model="password" :type="showPassword ? 'text' : 'password'" required class="w-full bg-slate-900/50 border border-slate-800 rounded-xl py-4 pl-12 pr-12 text-slate-100 placeholder:text-slate-600 focus:outline-none input-focus transition-all duration-300" placeholder="••••••••" />
                <button @click.prevent="showPassword = !showPassword" class="absolute right-1 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors" type="button">
                  <span class="material-symbols-outlined text-[20px]">{{ showPassword ? 'visibility_off' : 'visibility' }}</span>
                </button>
              </div>
              <p class="font-mono text-[10px] text-slate-600 mt-1 uppercase tracking-widest text-right">Encrypted Session: v2.0.4</p>
            </div>

            <!-- Action Button -->
            <div class="pt-4">
              <button :disabled="isLoading" class="gradient-button w-full py-4 rounded-xl text-white font-bold tracking-widest uppercase text-sm hover:brightness-110 disabled:opacity-50 transition-all duration-300 flex items-center justify-center gap-2" type="submit">
                {{ isLoading ? 'Entrando...' : 'Entrar' }}
                <span v-if="!isLoading" class="material-symbols-outlined text-[18px]">arrow_forward</span>
              </button>
            </div>
          </form>

          <!-- Footer Links -->
          <div class="mt-10 text-center space-y-4">
            <div class="flex items-center gap-4">
              <div class="h-[1px] flex-1 bg-slate-800"></div>
              <span class="text-[10px] font-mono text-slate-600 uppercase tracking-widest">Opciones</span>
              <div class="h-[1px] flex-1 bg-slate-800"></div>
            </div>
            <p class="text-sm">
              <span class="text-[#6b6b80]">¿No tiene acceso?</span>
              <router-link to="/signup" class="text-[#6b6b80] font-bold hover:text-primary transition-colors ml-1 underline underline-offset-4 decoration-primary/30">Crear cuenta para Cliente</router-link>
            </p>
          </div>
        </div>

        <!-- System Status Footer -->
        <div class="mt-8 flex justify-between items-center px-2 opacity-50">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            <span class="font-mono text-[10px] uppercase tracking-tighter text-slate-400">Servidores Activos</span>
          </div>
          <span class="font-mono text-[10px] text-slate-400 uppercase tracking-tighter">© 2024 FACTURACIÓN OCR</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();

const username = ref('');
const password = ref('');
const showPassword = ref(false);
const errorMsg = ref('');
const isLoading = ref(false);

const doLogin = async () => {
    errorMsg.value = '';
    isLoading.value = true;
    try {
        const res = await fetch(`/login?username=${encodeURIComponent(username.value)}&password=${encodeURIComponent(password.value)}`, {
            method: 'POST'
        });

        const data = await res.json();

        if (res.ok) {
            localStorage.setItem('token', data.access_token);
            router.push('/dashboard');
        } else {
            errorMsg.value = data.detail || 'Credenciales inválidas';
        }
    } catch (error) {
        errorMsg.value = 'Error de conexión';
    } finally {
        isLoading.value = false;
    }
};
</script>

<style>
.glass-card {
    background: #0d0d14;
    border: 1px solid rgba(255, 255, 255, 0.07);
    box-shadow: 0 0 40px rgba(149, 81, 251, 0.1);
}

.gradient-button {
    background: linear-gradient(135deg, #7c4dff 0%, #4d9fff 100%);
    box-shadow: 0 4px 15px rgba(124, 77, 255, 0.4);
}

.input-focus:focus {
    border-color: #4d9fff;
    box-shadow: 0 0 0 2px rgba(77, 159, 255, 0.2);
}
</style>
