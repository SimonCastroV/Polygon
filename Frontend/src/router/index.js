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
    // Cada estación entra con su propio rol: 'produccion' consulta y libera
    // las OP, 'picky' solo ve las que Producción ya liberó (ver PuedeVerOP
    // y ordenes_visibles_para en el backend). Las demás estaciones (Pesaje,
    // Mezcla, etc.) se irán sumando cuando se construya cada base.
    meta: {
      requiresAuth: true,
      rolesPermitidos: ['admin', 'supervisor', 'produccion', 'picky'],
    },
    children: [
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
