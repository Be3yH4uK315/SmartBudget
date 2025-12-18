import { Theme } from '@mui/material'

export const STATUS_STYLES: Record<
  string,
  (theme: Theme) => { borderColor: string; statusColor: string; pieColor: string }
> = {
  achieved: (theme: Theme) => ({
    borderColor: theme.palette.success.main,
    statusColor: theme.palette.success.main,
    pieColor: theme.palette.success.main,
  }),
  closed: (theme: Theme) => ({
    borderColor: theme.palette.gray.main,
    statusColor: theme.palette.text.primary,
    pieColor: theme.palette.gray.main,
  }),
  ongoing: (theme: Theme) => ({
    borderColor: theme.palette.surface.light,
    statusColor: theme.palette.success.main,
    pieColor: theme.palette.primary.main,
  }),
  expired: (theme: Theme) => ({
    borderColor: theme.palette.error.main,
    statusColor: theme.palette.error.main,
    pieColor: theme.palette.primary.main,
  }),
}
