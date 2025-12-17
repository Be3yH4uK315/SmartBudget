import { defineConfig } from '@rsbuild/core'
import { pluginReact } from '@rsbuild/plugin-react'
import { pluginTypeCheck } from '@rsbuild/plugin-type-check'

export default defineConfig({
  html: {
    favicon: './public/favicon.ico',
    template: './public/index.html',
  },
  output: {
    distPath: {
      root: 'build',
    },
  },
  plugins: [pluginReact(), pluginTypeCheck()],
})
