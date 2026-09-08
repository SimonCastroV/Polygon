import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/usuarios/Login.vue'),
  },
  {
    path: '/pendiente',
    name: 'pendiente',
    component: () => import('../views/Pendiente.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    component: () => import('../layouts/AdminLayout.vue'),
    // Cada estación y Supervisor de Pesaje tienen rutas y colas propias.
    // El backend aplica también permisos y filtros por estado.
    meta: {
      requiresAuth: true,
      rolesPermitidos: [
        'admin',
        'supervisor',
        'produccion',
        'picky',
        'pesaje',
        'supervisor_pesaje',
      ],
    },
    children: [
      {
        path: 'supervision-pesaje/ordenes',
        name: 'supervision-pesaje-ordenes',
        component: () => import('../views/pesaje/OrdenesPesaje.vue'),
        meta: { rolesPermitidos: ['supervisor_pesaje'] },
      },
      {
        path: 'supervision-pesaje/ordenes/:id',
        name: 'supervision-pesaje-detalle',
        component: () => import('../views/pesaje/OrdenPesajeDetalle.vue'),
        meta: { rolesPermitidos: ['supervisor_pesaje'] },
      },
      {
        path: '',
        redirect: () => {
          const auth = useAuthStore()
          return destinoSegunRol(auth.rol)
        },
      },
      {
        path: 'usuarios',
        name: 'admin-usuarios',
        component: () => import('../views/usuarios/GestionUsuarios.vue'),
        meta: { rolesPermitidos: ['admin'] },
      },
      {
        path: 'produccion/ordenes',
        name: 'admin-ordenes-produccion',
        component: () => import('../views/produccion/OrdenesProduccion.vue'),
        meta: { rolesPermitidos: ['admin', 'supervisor', 'produccion'] },
      },
      {
        path: 'produccion/ordenes/:id',
        name: 'admin-orden-detalle',
        component: () => import('../views/produccion/OrdenProduccionDetalle.vue'),
        meta: { rolesPermitidos: ['admin', 'supervisor', 'produccion'] },
      },
      {
        path: 'picky/ordenes',
        name: 'picky-ordenes',
        component: () => import('../views/picky/OrdenesPicky.vue'),
        meta: { rolesPermitidos: ['picky'] },
      },
      {
        path: 'picky/ordenes/:id',
        name: 'picky-orden-detalle',
        component: () => import('../views/picky/OrdenPickyDetalle.vue'),
        meta: { rolesPermitidos: ['picky'] },
      },
      {
        path: 'pesaje/ordenes',
        name: 'pesaje-ordenes',
        component: () => import('../views/pesaje/OrdenesPesaje.vue'),
        meta: { rolesPermitidos: ['pesaje'] },
      },
      {
        path: 'pesaje/ordenes/:id',
        name: 'pesaje-orden-detalle',
        component: () => import('../views/pesaje/OrdenPesajeDetalle.vue'),
        meta: { rolesPermitidos: ['pesaje'] },
      },
    ],
  },
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export function destinoSegunRol(rol) {
  if (rol === 'admin') return { name: 'admin-usuarios' }
  if (rol === 'supervisor' || rol === 'produccion') return { name: 'admin-ordenes-produccion' }
  if (rol === 'picky') return { name: 'picky-ordenes' }
  if (rol === 'supervisor_pesaje') return { name: 'supervision-pesaje-ordenes' }
  if (rol === 'pesaje') return { name: 'pesaje-ordenes' }

  return { name: 'pendiente' }
}

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.name === 'login' && auth.isAuthenticated) {
    return destinoSegunRol(auth.rol)
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login' }
  }

  if (to.meta.rolesPermitidos && !to.meta.rolesPermitidos.includes(auth.rol)) {
    return { name: 'pendiente' }
  }

  return true
})

export default router
