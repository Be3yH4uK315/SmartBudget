import { JSX } from 'react'
import { SxProps } from '@mui/material'

export type IconButtonItem = {
  Icon?: JSX.Element
  title?: string
  subtitle?: string
  path?: string
  onClick?: () => void
  paperSx?: SxProps
}
