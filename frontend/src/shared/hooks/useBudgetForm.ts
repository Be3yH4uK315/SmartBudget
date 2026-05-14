import { useMemo, useState } from 'react'
import { CATEGORIES_ICONS_MAP } from '@shared/constants'
import { CategoryRow, FormValues } from '@shared/types/components'

const fromPercent = (total: number | null, percent?: number) => {
  if (total == null || total <= 0) return undefined
  if (percent == null) return undefined

  return Math.round((total * percent) / 100)
}

const fromAmount = (total: number | null, limit?: number) => {
  if (total == null || total <= 0) return undefined
  if (limit == null) return undefined

  return Math.round((limit / total) * 100)
}

export const useBudgetForm = (initValues?: FormValues) => {
  const [values, setValues] = useState<FormValues>({
    totalLimitAmount: null,
    isAutoRenew: true,
    categories: [],
    ...initValues,
  })

  const resetInitValues = (init: FormValues) => {
    setValues(init)
  }

  const selectedCategoryIds = useMemo(
    () => values.categories.map((c) => c.categoryId).filter(Boolean) as number[],
    [values.categories],
  )

  const availableCategories = useMemo(
    () => Array.from(CATEGORIES_ICONS_MAP.keys()).filter((id) => !selectedCategoryIds.includes(id)),
    [selectedCategoryIds],
  )

  const totalPercent = useMemo(
    () => values.categories.reduce((sum, c) => sum + (c.percent ?? 0), 0),
    [values.categories],
  )

  const remainingPercent = Math.max(0, 100 - totalPercent)

  const isPercentOverflow = values.totalLimitAmount != null && totalPercent > 100

  const canSubmit = () =>
    !isPercentOverflow &&
    ((values.totalLimitAmount !== null && values.totalLimitAmount !== 0) ||
      values.categories.some((c) => c.limitAmount && c.limitAmount > 0))

  const setTotalLimit = (limit: number) => {
    setValues((prev) => {
      if (!limit) {
        return {
          ...prev,
          totalLimitAmount: null,
          categories: prev.categories.map((c) => ({
            ...c,
            percent: undefined,
          })),
        }
      }

      return {
        ...prev,
        totalLimitAmount: limit,
        categories: prev.categories.map((c) => {
          if (c.mode === 'percent' && c.percent != null) {
            return { ...c, limitAmount: fromPercent(limit, c.percent) }
          }

          if (c.mode === 'amount' && c.limitAmount != null) {
            return { ...c, percent: fromAmount(limit, c.limitAmount) }
          }

          return c
        }),
      }
    })
  }

  const addCategory = (value: number) => {
    setValues((prev) => ({
      ...prev,
      categories: [
        ...prev.categories,
        { categoryId: value, limitAmount: undefined, percent: undefined },
      ],
    }))
  }

  const removeCategory = (id: number) => {
    setValues((prev) => ({
      ...prev,
      categories: prev.categories.filter((c) => c.categoryId !== id),
    }))
  }

  const updateCategory = (index: number, patch: Partial<CategoryRow>) => {
    setValues((prev) => {
      const categories = [...prev.categories]
      categories[index] = { ...categories[index], ...patch }
      return { ...prev, categories }
    })
  }

  const updateAmount = (index: number, limitAmount: number) => {
    updateCategory(index, {
      limitAmount,
      mode: 'amount',
      percent: values.totalLimitAmount
        ? fromAmount(values.totalLimitAmount, limitAmount)
        : undefined,
    })
  }

  const updatePercent = (index: number, percent: number) => {
    updateCategory(index, {
      percent,
      mode: 'percent',
      limitAmount: values.totalLimitAmount
        ? fromPercent(values.totalLimitAmount, percent)
        : undefined,
    })
  }

  const toggleAutoRenew = (value: boolean) => {
    setValues((prev) => ({ ...prev, isAutoRenew: value }))
  }

  return {
    values,
    availableCategories,
    totalPercent,
    remainingPercent,
    isPercentOverflow,
    canSubmit,
    resetInitValues,
    setTotalLimit,
    addCategory,
    removeCategory,
    updateCategory,
    updateAmount,
    updatePercent,
    toggleAutoRenew,
  }
}
