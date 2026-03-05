import { createRouter, createWebHistory } from 'vue-router'
import IniciarSesion from '../views/iniciar_sesion.vue'
import Registrarse from '../views/registrarse.vue'
import AdminDashboard from '../views/admin_dashboard.vue'
import BusinessProfile from '../views/business_profile.vue'
import ConfigProfile from '../views/config_perfil.vue'
import EmitirFactura from '../views/negocio_emitir_factura.vue'
import FacturarGastos from '../views/negocio_facturar_gastos.vue'
import MisClientes from '../views/negocio_mis_clientes.vue'
import MisFacturas from '../views/negocio_mis_facturas.vue'

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
        },
        {
            path: '/admin',
            name: 'Admin',
            component: AdminDashboard
        },
        {
            path: '/business-profile',
            name: 'Business Profile',
            component: BusinessProfile
        },
        {
            path: '/config-profile',
            name: 'Config Profile',
            component: ConfigProfile
        },
        {
            path: '/emitir-factura',
            name: 'Emitir Factura',
            component: EmitirFactura
        },
        {
            path: '/facturar-gastos',
            name: 'Facturar Gastos',
            component: FacturarGastos
        },
        {
            path: '/mis-clientes',
            name: 'Mis Clientes',
            component: MisClientes
        },
        {
            path: '/mis-facturas',
            name: 'Mis Facturas',
            component: MisFacturas
        }

    ],
})

export default router