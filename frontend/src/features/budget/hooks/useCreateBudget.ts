import { useMemo, useState } from 'react'
import { CATEGORIES_ICONS_MAP } from '@shared/constants/categoriesIcons'

export type CategoryRow = {
  categoryId: number
  limit: number
  percent?: number
}

type FormValues = {
  totalLimit: number
  isAutoRenew: boolean
  categories: CategoryRow[]
}

const fromPercent = (total: number, percent: number) => Math.round((total * percent) / 100)

const fromAmount = (total: number, limit: number) => (total ? Math.round((limit / total) * 100) : 0)

export const useCreateBudget = () => {
  const [values, setValues] = useState<FormValues>({
    totalLimit: 0,
    isAutoRenew: true,
    categories: [],
  })

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

  const isPercentOverflow = values.totalLimit > 0 && totalPercent > 100

  const canSubmit =
    !isPercentOverflow && (values.totalLimit > 0 || values.categories.some((c) => c.limit > 0))

  const setTotalLimit = (limit: number) => {
    setValues((prev) => ({
      ...prev,
      totalLimit: limit,
      categories: prev.categories.map((c) => ({
        ...c,
        limit: c.percent != null ? fromPercent(limit, c.percent) : c.limit,
      })),
    }))
  }

  const addCategory = () => {
    setValues((prev) => ({
      ...prev,
      categories: [...prev.categories, { categoryId: 0, limit: 0, percent: 0 }],
    }))
  }

  const removeCategory = (index: number) => {
    setValues((prev) => ({
      ...prev,
      categories: prev.categories.filter((_, i) => i !== index),
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
      percent: values.totalLimit ? fromAmount(values.totalLimit, limit) : undefined,
    })
  }

  const updatePercent = (index: number, percent: number) => {
    updateCategory(index, {
      percent,
      limit: fromPercent(values.totalLimit, percent),
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

    setTotalLimit,
    addCategory,
    removeCategory,
    updateCategory,
    updateAmount,
    updatePercent,
    toggleAutoRenew,
  }
}
