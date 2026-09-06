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
    meta: { requiresAuth: true, rolesPermitidos: ['admin'] },
    children: [
      {
        path: '',
        redirect: { name: 'admin-usuarios' },
      },
      {
        path: 'usuarios',
        name: 'admin-usuarios',
        component: () => import('../views/usuarios/GestionUsuarios.vue'),
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

function destinoSegunRol(rol) {
  return rol === 'admin' ? { name: 'admin-usuarios' } : { name: 'pendiente' }
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
