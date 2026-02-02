import { useState } from 'react'
import {
  getTransactions,
  resetFilters,
  setCategoryIds,
  setDateFrom,
  setDateTo,
  setType,
  setValueFrom,
  setValueTo,
} from '@features/transactions/store'
import { TransactionsFilters, TransactionType } from '@features/transactions/types'
import { parseCategoryIds } from '@features/transactions/utils'
import { SelectChangeEvent } from '@mui/material'
import { useAppDispatch } from '@shared/store'
import { isSetsEqual } from '@shared/utils'
import dayjs from 'dayjs'
import { useSearchParams } from 'react-router'

export function useTransactionsFilters(filters: TransactionsFilters) {
  const dispatch = useAppDispatch()

  const [searchParams, setSearchParams] = useSearchParams()

  const categoryParam = searchParams.get('categoriesIds')
  const initialCategoryIds = parseCategoryIds(categoryParam?.split(',') ?? [])

  const [localCategoryIds, setLocalCategoryIds] = useState<string[]>(initialCategoryIds.map(String))
  const [localType, setLocalType] = useState<TransactionType | ''>(filters.type)
  const [localDateFrom, setLocalDateFrom] = useState<string>(filters.dateFrom)
  const [localDateTo, setLocalDateTo] = useState<string>(filters.dateTo)
  const [localValueFrom, setLocalValueFrom] = useState<number | undefined>(filters.valueFrom)
  const [localValueTo, setLocalValueTo] = useState<number | undefined>(filters.valueTo)

  const dirty =
    filters.categoryIds.length > 0 ||
    filters.type !== '' ||
    filters.valueFrom !== undefined ||
    filters.valueTo !== undefined ||
    filters.dateFrom !== '' ||
    filters.dateTo !== ''

  const handleCategoryIdsChange = (e: SelectChangeEvent<string[]>) => {
    const value = e.target.value
    setLocalCategoryIds(typeof value === 'string' ? value.split(',') : value)
  }

  const handleTypeChange = (e: SelectChangeEvent<string>) => {
    const value = e.target.value
    setLocalType(value as TransactionType | '')

    if (value === filters.type) return

    dispatch(setType(value as TransactionType | ''))
    dispatch(getTransactions())
  }

  const handleDateFromChange = (value: string) => setLocalDateFrom(value)
  const handleDateToChange = (value: string) => setLocalDateTo(value)
  const handleValueFromChange = (value?: number) => setLocalValueFrom(value)
  const handleValueToChange = (value?: number) => setLocalValueTo(value)

  const handleApplyCategories = () => {
    const categoriesIds = parseCategoryIds(localCategoryIds)

    if (isSetsEqual(categoriesIds, filters.categoryIds)) return

    dispatch(setCategoryIds(categoriesIds))
    dispatch(getTransactions())

    const next = new URLSearchParams(searchParams)

    if (categoriesIds.length > 0) next.set('categoriesIds', categoriesIds.join(','))
    else next.delete('categoriesIds')

    setSearchParams(next, { replace: true })
  }

  const handleApplyValues = () => {
    if (localValueFrom === filters.valueFrom && localValueTo === filters.valueTo) return

    if (localValueFrom && localValueTo && localValueFrom > localValueTo) {
      handleValueFromChange(localValueTo)
      handleValueToChange(localValueFrom)

      dispatch(setValueFrom(localValueTo))
      dispatch(setValueTo(localValueFrom))
      dispatch(getTransactions())
      return
    }

    dispatch(setValueFrom(localValueFrom))
    dispatch(setValueTo(localValueTo))
    dispatch(getTransactions())
  }

  const handleApplyDates = () => {
    if (localDateFrom === filters.dateFrom && localDateTo === filters.dateTo) return

    if (localDateFrom && localDateTo && dayjs(localDateFrom).isAfter(dayjs(localDateTo))) {
      handleDateFromChange(localDateTo)
      handleDateToChange(localDateFrom)

      dispatch(setDateFrom(localDateTo))
      dispatch(setDateTo(localDateFrom))
      dispatch(getTransactions())
      return
    }

    dispatch(setDateFrom(localDateFrom))
    dispatch(setDateTo(localDateTo))
    dispatch(getTransactions())
  }

  const handleRemoveCategoryId = (categoryId: string) => {
    if (filters.categoryIds.length === 0) return

    const next = localCategoryIds.filter((id) => id !== categoryId)
    setLocalCategoryIds(next)

    const categoriesIds = parseCategoryIds(next)
    dispatch(setCategoryIds(categoriesIds))
    dispatch(getTransactions())

    const nextParam = new URLSearchParams(searchParams)

    if (categoriesIds.length > 0) nextParam.set('categoriesIds', categoriesIds.join(','))
    else nextParam.delete('categoriesIds')

    setSearchParams(nextParam, { replace: true })
  }

  const handleClearFilters = () => {
    if (!dirty) return

    setLocalCategoryIds([])
    setLocalType('')
    setLocalDateFrom('')
    setLocalDateTo('')
    setLocalValueFrom(undefined)
    setLocalValueTo(undefined)

    dispatch(resetFilters())
    dispatch(getTransactions())

    const next = new URLSearchParams(searchParams)
    next.delete('categoriesIds')
    setSearchParams(next, { replace: true })
  }

  return {
    dirty,
    localCategoryIds,
    localType,
    localDateFrom,
    localDateTo,
    localValueFrom,
    localValueTo,
    setLocalType,
    setLocalValueFrom,
    setLocalValueTo,
    setLocalDateFrom,
    setLocalDateTo,
    handleCategoryIdsChange,
    handleTypeChange,
    handleDateFromChange,
    handleDateToChange,
    handleValueFromChange,
    handleValueToChange,
    handleApplyCategories,
    handleApplyValues,
    handleApplyDates,
    handleRemoveCategoryId,
    handleClearFilters,
  }
}
