import { Theme } from '@mui/material'

export const STATUS_STYLES: Record<
  string,
  (theme: Theme) => { statusColor: string; pieColor: string }
> = {
  achieved: (theme: Theme) => ({
    statusColor: theme.palette.success.main,
    pieColor: theme.palette.success.main,
  }),
  closed: (theme: Theme) => ({
    statusColor: theme.palette.text.primary,
    pieColor: theme.palette.gray.main,
  }),
  ongoing: (theme: Theme) => ({
    statusColor: theme.palette.success.main,
    pieColor: theme.palette.primary.main,
  }),
  expired: (theme: Theme) => ({
    statusColor: theme.palette.error.main,
    pieColor: theme.palette.primary.main,
  }),
}
