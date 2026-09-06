import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import configPrettier from 'eslint-config-prettier'
import globals from 'globals'

export default [
  { ignores: ['dist/**', 'node_modules/**'] },

  js.configs.recommended,
  ...pluginVue.configs['flat/recommended'],

  {
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    rules: {
      // Convenciones de nombres: camelCase para variables/funciones JS,
      // PascalCase para componentes Vue y kebab-case para props/eventos
      // en el template (estas ultimas ya las trae 'flat/recommended').
      camelcase: ['warn', { properties: 'never' }],
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],

      // Las vistas de pagina (Login.vue, Pendiente.vue, Badge.vue) usan
      // nombres de una sola palabra a proposito; el riesgo de colision
      // con elementos HTML nativos que previene esta regla no aplica aqui.
      'vue/multi-word-component-names': 'off',
    },
  },

  // Debe ir al final: desactiva reglas de estilo de ESLint/Vue que
  // Prettier ya resuelve, para que no compitan entre si.
  configPrettier,
]
