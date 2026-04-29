import { useCallback, useMemo, useState } from 'react'
import { useTheme } from '@mui/material'
import { useTranslate } from '@shared/hooks'
import { FilterType, PieDataItem, TransactionBase } from '@shared/types/components'

export function useTransactionFilters<T>(
  data: T[],
  mapper: (dataItem: T) => TransactionBase,
  initType: 'expense' | 'income',
) {
  const translateCategory = useTranslate('Categories')
  const translateMonth = useTranslate('MonthTransactionBlockLabel')
  const theme = useTheme()

  const [activeType, setActiveType] = useState<FilterType>(initType)

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
      normalizedData: [] as PieDataItem[],
      total: 0,
      count: 0,
    }

    const acc = data.reduce((acc, c) => {
      const item = mapper(c)
      if (item.value <= 0 || item.type !== activeType) return acc

      const color = colors[acc.count % colors.length]

      acc.normalizedData.push({
        value: item.value,
        label: item.categoryId
          ? translateCategory(item.categoryId)
          : item.month
            ? translateMonth(item.month)
            : '',
        color: color.main,
        lightColor: color.light,
      })

      acc.total += item.value
      acc.count++

      return acc
    }, init)

    return { normalizedData: acc.normalizedData, total: acc.total }
  }, [data, activeType, colors, translateCategory, translateMonth, mapper])

  return { activeType, toggleFilter, normalizedData, total }
}
