import { useCallback, useMemo, useState } from 'react'
import { DashboardCategory, FilterType, normalizedCategory } from '@features/dashboard/types'
import { useTheme } from '@mui/material'
import { useTranslate } from '@shared/hooks'

export function useTransactionFilters(data: DashboardCategory[]) {
  const translateCategory = useTranslate('Categories')
  const theme = useTheme()

  const [activeType, setActiveType] = useState<FilterType>('expense')

  const toggleFilter = useCallback((type: FilterType) => {
    setActiveType(type)
  }, [])

  const colors = useMemo(
    () => [
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
    ],
    [theme],
  )

  const { normalizedData, total } = useMemo(() => {
    const init = {
      normalizedData: [] as normalizedCategory[],
      total: 0,
      count: 0,
    }

    const acc = data.reduce((acc, c) => {
      const value = Number(c.value)
      if (value <= 0 || c.type !== activeType) return acc

      const color = colors[acc.count % colors.length]

      acc.normalizedData.push({
        value,
        label: translateCategory(String(c.categoryId)),
        color: color.main,
        lightColor: color.light,
      })

      acc.total += value
      acc.count++

      return acc
    }, init)

    return { normalizedData: acc.normalizedData, total: acc.total }
  }, [data, activeType, translateCategory, colors])

  return { activeType, toggleFilter, normalizedData, total }
}
