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
    totalLimit: null,
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

  const isPercentOverflow = values.totalLimit != null && totalPercent > 100

  const canSubmit = () =>
    !isPercentOverflow &&
    ((values.totalLimit !== null && values.totalLimit !== 0) ||
      values.categories.some((c) => c.limit && c.limit > 0))

  const setTotalLimit = (limit: number) => {
    setValues((prev) => {
      if (!limit) {
        return {
          ...prev,
          totalLimit: null,
          categories: prev.categories.map((c) => ({
            ...c,
            percent: undefined,
          })),
        }
      }

      return {
        ...prev,
        totalLimit: limit,
        categories: prev.categories.map((c) => {
          if (c.mode === 'percent' && c.percent != null) {
            return { ...c, limit: fromPercent(limit, c.percent) }
          }

          if (c.mode === 'amount' && c.limit != null) {
            return { ...c, percent: fromAmount(limit, c.limit) }
          }

          return c
        }),
      }
    })
  }

  const addCategory = (value: number) => {
    setValues((prev) => ({
      ...prev,
      categories: [...prev.categories, { categoryId: value, limit: undefined, percent: undefined }],
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

  const updateAmount = (index: number, limit: number) => {
    updateCategory(index, {
      limit,
      mode: 'amount',
      percent: values.totalLimit ? fromAmount(values.totalLimit, limit) : undefined,
    })
  }

  const updatePercent = (index: number, percent: number) => {
    updateCategory(index, {
      percent,
      mode: 'percent',
      limit: values.totalLimit ? fromPercent(values.totalLimit, percent) : undefined,
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
