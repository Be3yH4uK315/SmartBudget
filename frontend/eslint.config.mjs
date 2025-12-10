import { fixupConfigRules, fixupPluginRules } from '@eslint/compat'
import { FlatCompat } from '@eslint/eslintrc'
import js from '@eslint/js'
import typescriptEslint from '@typescript-eslint/eslint-plugin'
import tsParser from '@typescript-eslint/parser'
import { defineConfig, globalIgnores } from 'eslint/config'
import _import from 'eslint-plugin-import'
import react from 'eslint-plugin-react'
import reactHooks from 'eslint-plugin-react-hooks'
import simpleImportSort from 'eslint-plugin-simple-import-sort'
import globals from 'globals'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all,
})

export default defineConfig([
  globalIgnores([
    '**/node_modules',
    '**/build',
    '**/assets',
    '**/*.css',
    'src/languages/**/*.json',
  ]),
  {
    extends: fixupConfigRules(
      compat.extends(
        'eslint:recommended',
        'plugin:react/recommended',
        'plugin:@typescript-eslint/recommended',
        'plugin:react-hooks/recommended',
        'plugin:prettier/recommended',
      ),
    ),

    plugins: {
      react: fixupPluginRules(react),
      '@typescript-eslint': fixupPluginRules(typescriptEslint),
      'react-hooks': fixupPluginRules(reactHooks),
      'simple-import-sort': simpleImportSort,
      import: fixupPluginRules(_import),
    },

    languageOptions: {
      globals: {
        ...globals.browser,
      },

      parser: tsParser,
      ecmaVersion: 12,
      sourceType: 'module',

      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },

    settings: {
      react: {
        version: 'detect',
      },
    },

    rules: {
      'react/react-in-jsx-scope': 'off',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
      '@typescript-eslint/no-empty-interface': 'off',
      '@typescript-eslint/no-namespace': 'off',

      '@typescript-eslint/no-unused-vars': [
        'warn',
        {
          caughtErrors: 'none',
        },
      ],

      '@typescript-eslint/no-empty-object-type': [
        'warn',
        {
          allowInterfaces: 'with-single-extends',
        },
      ],

      'react/display-name': 'off',

      'no-empty': [
        'error',
        {
          allowEmptyCatch: true,
        },
      ],

      'react/prop-types': 'off',

      'import/no-duplicates': [
        'error',
        {
          'prefer-inline': true,
        },
      ],

      'simple-import-sort/imports': [
        'error',
        {
          groups: [['^react$', '^\\u0000', '^@?\\w', '^', '^\\.']],
        },
      ],

      'simple-import-sort/exports': 'error',
      'prettier/prettier': ['warn'],
    },
  },
])
