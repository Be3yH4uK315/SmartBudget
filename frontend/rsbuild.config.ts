import { defineConfig } from '@rsbuild/core'
import { pluginReact } from '@rsbuild/plugin-react'
import { pluginTypeCheck } from '@rsbuild/plugin-type-check'

export default defineConfig({
  html: {
    favicon: './public/icons/favicon.ico',
    template: './public/index.html',
  },
  output: {
    distPath: {
      root: 'dist',
    },
  },
  plugins: [pluginReact(), pluginTypeCheck()],
})
