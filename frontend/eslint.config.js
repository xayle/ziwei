import pluginJs from '@eslint/js'
import globals from 'globals'
import pluginVue from 'eslint-plugin-vue'
import tsParser from '@typescript-eslint/parser'
import tsPlugin from '@typescript-eslint/eslint-plugin'

export default [
  // Base JS recommended rules
  pluginJs.configs.recommended,

  // Vue 3 essential rules
  ...pluginVue.configs['flat/essential'],

  // TypeScript + Vue source files
  {
    files: ['src/**/*.{ts,vue}'],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.es2022,
      },
      parser: (await import('vue-eslint-parser')).default,
      parserOptions: {
        parser: tsParser,
        ecmaVersion: 'latest',
        sourceType: 'module',
        extraFileExtensions: ['.vue'],
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
    },
    rules: {
      // TypeScript
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],

      // Vue
      'vue/multi-word-component-names': 'off',
      'vue/no-v-html': 'warn',

      // General
      'no-console': ['warn', { allow: ['warn', 'error'] }],
      'no-unused-vars': 'off', // handled by TS plugin
      'no-undef': 'off', // TypeScript handles this
      'no-empty': 'warn', // empty catch blocks are common in resilient code
      'no-useless-assignment': 'warn',
      'no-irregular-whitespace': 'warn',
    },
  },

  // Test files — relaxed rules
  {
    files: ['**/__tests__/**/*.{ts,js}', '**/*.spec.{ts,js}'],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.es2022,
      },
    },
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      'no-console': 'off',
    },
  },

  // Ignore patterns
  {
    ignores: ['dist/', 'node_modules/', 'coverage/'],
  },
]
