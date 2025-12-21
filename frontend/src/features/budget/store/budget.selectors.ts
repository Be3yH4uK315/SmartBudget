import { createSelector } from '@reduxjs/toolkit'
import { createLazySliceStateSelector } from '@shared/utils/store'
import { Category } from '../types'
import { getBudgetInitialState } from './budget.state'

const sliceStateSelector = createLazySliceStateSelector('budget', getBudgetInitialState())

export const selectBudgetCategories = sliceStateSelector((state) => state.categories)

export const selectIsAutoRenew = sliceStateSelector((state) => state.isAutoRenew)

export const selectBudgetCurrentValue = sliceStateSelector((state) => state.currentValue)

export const selectBudgetTotalLimit = sliceStateSelector((state) => state.totalLimit)

export const selectIsBudgetLoading = sliceStateSelector((state) => state.currentValue)

export const selectCategoriesWithLimits = createSelector(selectBudgetCategories, (categories) => {
  const init = {
    limitedCount: 0,
    limited: [],
    unlimited: [],
    incomeCategory: {
      categoryId: 31,
      limit: 0,
      currentValue: 0,
    },
  }

  const { limitedCount, limited, unlimited, incomeCategory } = categories.reduce<{
    limitedCount: number
    limited: Category[]
    unlimited: Category[]
    incomeCategory: Category
  }>((acc, c) => {
    if (c.categoryId === 31) {
      acc.incomeCategory.currentValue = c.currentValue
      return acc
    }

    if (c.limit > 0) {
      acc.limited.push(c)
      acc.limitedCount += 1
    } else {
      acc.unlimited.push(c)
    }

    return acc
  }, init)

  return { limitedCount, limited, unlimited, incomeCategory }
})

export const selectOverflowCategories = createSelector(selectBudgetCategories, (categories) => {
  const init = { preOverflow: [], overflow: [] }

  const { preOverflow, overflow } = categories.reduce<{
    preOverflow: Category[]
    overflow: Category[]
  }>((acc, c) => {
    if (c.limit === 0 || c.categoryId === 31) return acc

    const ratio = c.currentValue / c.limit

    if (ratio >= 1) {
      acc.overflow.push(c)
    } else if (ratio >= 0.8) {
      acc.preOverflow.push(c)
    }

    return acc
  }, init)

  return { preOverflow, overflow }
})
