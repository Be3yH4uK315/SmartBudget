import { ComponentType } from 'react'
import { SvgIconProps } from '@mui/material'

export type FeatureCard = {
  Icon: ComponentType<SvgIconProps>
  title: string
  subtitle: string
}
