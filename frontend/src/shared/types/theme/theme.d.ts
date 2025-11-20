import { PaletteOptions as MuiPaletteOptions } from '@mui/material/styles'
import '@mui/material/Button'

declare module '@mui/material/Button' {
  interface ButtonPropsVariantOverrides {
    gray: true
    yellow: true
    blue: true
    link: true
  }
}

declare module '@mui/material/styles' {
  interface Palette {
    gray: Palette['primary']
    surface: Palette['primary']
    link: Palette['primary']
    info: Palette['primary']
    text: Palette['primary']
    alert: Palette['primary']
    grayButton: Palette['primary']
    additionalRed: Palette['primary']
    additionalPurple: Palette['primary']
    additionalBlue: Palette['primary']
    additionalLavender: Palette['primary']
    additionalOrange: Palette['primary']
    additionalGray: Palette['primary']
  }

  interface PaletteOptions {
    gray: MuiPaletteOptions['primary']
    surface: MuiPaletteOptions['primary']
    link: MuiPaletteOptions['primary']
    info: MuiPaletteOptions['primary']
    text: MuiPaletteOptions['primary']
    alert: MuiPaletteOptions['primary']
    grayButton: MuiPaletteOptions['primary']
    additionalRed: MuiPaletteOptions['primary']
    additionalPurple: MuiPaletteOptions['primary']
    additionalBlue: MuiPaletteOptions['primary']
    additionalLavender: MuiPaletteOptions['primary']
    additionalOrange: MuiPaletteOptions['primary']
    additionalGray: MuiPaletteOptions['primary']
  }

  type SvgIconPropsColorOverrides = 'gray'
}
