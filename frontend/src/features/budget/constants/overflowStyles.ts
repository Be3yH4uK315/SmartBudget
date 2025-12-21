import { Theme } from '@mui/material'

export const OVERFLOW_STYLES: Record<
  string,
  (theme: Theme) => { borderColor: string; fontColor: string; bgColor: string }
> = {
  overflow: (theme: Theme) => ({
    borderColor: theme.palette.error.main,
    fontColor: theme.palette.error.dark,
    bgColor: theme.palette.error.light,
  }),
  preOverflow: (theme: Theme) => ({
    borderColor: theme.palette.alert.main,
    fontColor: theme.palette.alert.dark,
    bgColor: theme.palette.alert.light,
  }),
}
