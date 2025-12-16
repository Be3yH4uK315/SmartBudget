import { useState } from 'react'
import { SelectChangeEvent } from '@mui/material'
import { useSearchParams } from 'react-router'

export function useCategoryFilter() {
  const [searchParams, setSearchParams] = useSearchParams()

  const categoryIdFromUrl = searchParams.get('categoryId')
  const parsedCategoryId = categoryIdFromUrl ? Number(categoryIdFromUrl) : null

  const [selectedCategory, setSelectedCategory] = useState<number | null>(
    Number.isFinite(parsedCategoryId) ? parsedCategoryId : null,
  )

  const handleCategoryChange = (event: SelectChangeEvent<string>) => {
    const value = event.target.value

    const categoryId = value === '' ? null : Number(value)

    setSelectedCategory(categoryId)

    if (categoryId !== null) {
      setSearchParams({ categoryId: String(categoryId) })
    } else {
      setSearchParams({})
    }
  }
  return { selectedCategory, parsedCategoryId, handleCategoryChange, setSelectedCategory }
}
