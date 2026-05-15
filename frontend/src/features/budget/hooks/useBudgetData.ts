import { useMemo } from 'react'
import { Category } from '@features/budget/types'

type Props = {
  categories: Category[]
}

type BudgetData = {
  limitedSum: number
  limited: Category[]
  unlimited: Category[]
}

export const useBudgetData = ({ categories }: Props) => {
  const { limited, unlimited, limitedSum } = useMemo(() => {
    const init: BudgetData = {
      limitedSum: 0,
      limited: [],
      unlimited: [],
    }

    return categories.reduce((acc, c) => {
      if (c.transactionType === 'income') return acc

      if (c.limitAmount > 0) {
        acc.limited.push(c)
        acc.limitedSum += c.limitAmount
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
      const ratio = c.amount / c.limitAmount
      if (ratio >= 0.9) overflow.push(c)
      else if (ratio >= 0.8) preOverflow.push(c)
    })

    return { preOverflow, overflow }
  }, [limited])

  return {
    limited,
    unlimited,
    limitedSum,
    preOverflow,
    overflow,
  }
}
