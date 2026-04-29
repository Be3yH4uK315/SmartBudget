import { useMemo } from 'react'
import { INCOME_CATEGORY_ID } from '@features/budget/constants/incomeCategory'
import { Category } from '@features/budget/types'

type Props = {
  categories: Category[]
}

export const useBudgetData = ({ categories }: Props) => {
  const { limited, unlimited, limitedSum, incomeCategory } = useMemo(() => {
    const init = {
      limitedSum: 0,
      limited: [] as Category[],
      unlimited: [] as Category[],
      incomeCategory: { categoryId: INCOME_CATEGORY_ID, limit: 0, currentValue: 0 } as Category,
    }

    return categories.reduce((acc, c) => {
      if (c.categoryId === INCOME_CATEGORY_ID) {
        acc.incomeCategory.currentValue = c.currentValue
        return acc
      }

      if (c.limit > 0) {
        acc.limited.push(c)
        acc.limitedSum += c.limit
      } else {
        acc.unlimited.push(c)
      }

      return acc
    }, init)
  }, [categories])

  const { preOverflow, overflow } = useMemo(() => {
    const preOverflow: Category[] = []
    const overflow: Category[] = []

    limited.forEach((c) => {
      const ratio = c.currentValue / c.limit
      if (ratio >= 0.9) overflow.push(c)
      else if (ratio >= 0.8) preOverflow.push(c)
    })

    return { preOverflow, overflow }
  }, [limited])

  return {
    limited,
    unlimited,
    limitedSum,
    incomeCategory,
    preOverflow,
    overflow,
  }
}
