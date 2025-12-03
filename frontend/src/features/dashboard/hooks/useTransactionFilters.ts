import { useCallback, useMemo, useState } from 'react'
import { useTheme } from '@mui/material'
import { useTranslate } from '@shared/hooks'

export function useTransactionFilters(data: DashboardCategory[]) {
  const translateCategory = useTranslate('Categories')
  const theme = useTheme()

  const [activeType, setActiveType] = useState<FilterType>('expense')

  const toggleFilter = useCallback((type: FilterType) => {
    setActiveType(type)
  }, [])

  const { normalizedData, total }: { normalizedData: normalizedCategory[]; total: number } =
    useMemo(() => {
      const colors = [
        {
          main: theme.palette.additionalRed.main,
          light: theme.palette.additionalRed.light,
        },
        {
          main: theme.palette.additionalBlue.main,
          light: theme.palette.additionalBlue.light,
        },
        {
          main: theme.palette.additionalLavender.main,
          light: theme.palette.additionalLavender.light,
        },
        {
          main: theme.palette.additionalOrange.main,
          light: theme.palette.additionalOrange.light,
        },
        {
          main: theme.palette.additionalGray.main,
          light: theme.palette.additionalGray.light,
        },
        {
          main: theme.palette.additionalPurple.main,
          light: theme.palette.additionalPurple.light,
        },
      ]

      const normalizedData = data
        .filter((c) => Number(c.value) > 0)
        .filter((c) => c.type === activeType)
        .map((c, idx) => ({
          value: Number(c.value),
          label: translateCategory(`${c.categoryId}`),
          color: colors[idx % colors.length].main,
          lightColor: colors[idx % colors.length].light,
        }))

      return {
        normalizedData,
        total: normalizedData.reduce((sum, c) => sum + c.value, 0),
      }
    }, [data, activeType, theme, translateCategory])

  return { activeType, toggleFilter, normalizedData, total }
}
