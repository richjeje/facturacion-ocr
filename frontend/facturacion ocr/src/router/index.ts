import { createRouter, createWebHistory } from 'vue-router'
import IniciarSesion from '../views/iniciar_sesion.vue'
import Registrarse from '../views/registrarse.vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            name: 'Iniciar Sesion',
            component: IniciarSesion
        },
        {
            path: '/signup',
            name: 'Registrarse',
            component: Registrarse
        }

    ],
})

export default router