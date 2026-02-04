import { useRef, useState } from 'react'
import { clearTransactionsState, getTransactions } from '@features/transactions/store'
import { Category, TransactionsFilters, TransactionType } from '@features/transactions/types'
import { isSameFilters, parseCategoryIds } from '@features/transactions/utils'
import { SelectChangeEvent } from '@mui/material'
import { useAppDispatch } from '@shared/store'
import { isSetsEqual } from '@shared/utils/isSetsEqual'
import dayjs from 'dayjs'
import { useSearchParams } from 'react-router'

export function useTransactionsFilters() {
  const dispatch = useAppDispatch()

  const [searchParams, setSearchParams] = useSearchParams()

  const categoryParam = searchParams.get('categoriesIds')
  const initialCategoryIds = parseCategoryIds(categoryParam?.split(',') ?? [])

  const [localCategoryIds, setLocalCategoryIds] = useState<string[]>(initialCategoryIds.map(String))
  const [localType, setLocalType] = useState<TransactionType | ''>('')
  const [localDateFrom, setLocalDateFrom] = useState<string>('')
  const [localDateTo, setLocalDateTo] = useState<string>('')
  const [localValueFrom, setLocalValueFrom] = useState<number | undefined>()
  const [localValueTo, setLocalValueTo] = useState<number | undefined>()

  const appliedFiltersRef = useRef<TransactionsFilters>({
    categoryIds: initialCategoryIds,
    type: '',
    dateFrom: '',
    dateTo: '',
    valueFrom: undefined,
    valueTo: undefined,
  })

  const isDirty = () => {
    return !isSameFilters(appliedFiltersRef.current, {
      categoryIds: [],
      type: '',
      dateFrom: '',
      dateTo: '',
      valueFrom: undefined,
      valueTo: undefined,
    })
  }

  const applyFilters = (nextFilters: TransactionsFilters) => {
    appliedFiltersRef.current = nextFilters

    dispatch(clearTransactionsState())
    dispatch(getTransactions(nextFilters))
  }

  const handleCategoryIdsChange = (e: SelectChangeEvent<string[]> | string[]) => {
    const value = 'target' in e ? e.target.value : e
    setLocalCategoryIds(typeof value === 'string' ? value.split(',') : value)
  }

  const handleApplyCategories = (nextLocalCategoryIds?: string[]) => {
    const categoriesArray: Category[] = Array.isArray(nextLocalCategoryIds)
      ? parseCategoryIds(nextLocalCategoryIds)
      : parseCategoryIds(localCategoryIds)

    const nextFilters: TransactionsFilters = {
      ...appliedFiltersRef.current,
      categoryIds: categoriesArray,
    }

    if (isSetsEqual(appliedFiltersRef.current.categoryIds, categoriesArray)) return

    applyFilters(nextFilters)

    const params = new URLSearchParams(searchParams)
    if (categoriesArray.length) {
      params.set('categoriesIds', categoriesArray.join(','))
    } else {
      params.delete('categoriesIds')
    }
    setSearchParams(params, { replace: true })
  }

  const handleRemoveCategoryId = (categoryId: number) => {
    const nextLocal = localCategoryIds.filter((id) => id !== String(categoryId))

    setLocalCategoryIds(nextLocal)
    handleApplyCategories(nextLocal)
  }

  const handleTypeChange = (e: SelectChangeEvent<string>) => {
    const value = e.target.value as TransactionType | ''
    setLocalType(value)

    handleApplyType(value)
  }

  const handleApplyType = (newType?: TransactionType | '') => {
    const typeToApply = newType !== undefined ? newType : localType

    const nextFilters: TransactionsFilters = {
      ...appliedFiltersRef.current,
      type: typeToApply,
    }

    if (appliedFiltersRef.current.type === typeToApply) return

    applyFilters(nextFilters)
  }

  const handleDateFromChange = (value: string) => setLocalDateFrom(value)
  const handleDateToChange = (value: string) => setLocalDateTo(value)

  const handleApplyDates = (from?: string, to?: string) => {
    const fromToApply = from ?? localDateFrom
    const toToApply = to ?? localDateTo

    let finalFrom = fromToApply
    let finalTo = toToApply
    if (fromToApply && toToApply && dayjs(fromToApply).isAfter(dayjs(toToApply))) {
      finalFrom = toToApply
      finalTo = fromToApply
      setLocalDateFrom(finalFrom)
      setLocalDateTo(finalTo)
    }

    const nextFilters: TransactionsFilters = {
      ...appliedFiltersRef.current,
      dateFrom: finalFrom,
      dateTo: finalTo,
    }

    if (
      appliedFiltersRef.current.dateFrom === finalFrom &&
      appliedFiltersRef.current.dateTo === finalTo
    )
      return

    applyFilters(nextFilters)
  }

  const handleValueFromChange = (value?: number) => setLocalValueFrom(value)
  const handleValueToChange = (value?: number) => setLocalValueTo(value)

  const handleApplyValues = (from?: number, to?: number) => {
    const valueFromToApply = from ?? localValueFrom
    const valueToToApply = to ?? localValueTo

    //костыль для сброса через чипы, но вроде бы работает :)
    let finalValueFrom = valueFromToApply === -1 ? undefined : valueFromToApply
    let finalValueTo = valueToToApply === -1 ? undefined : valueToToApply

    if (
      valueFromToApply !== undefined &&
      valueFromToApply !== -1 &&
      valueToToApply !== undefined &&
      valueToToApply !== -1 &&
      valueFromToApply > valueToToApply
    ) {
      finalValueFrom = valueToToApply
      finalValueTo = valueFromToApply
      setLocalValueFrom(finalValueFrom)
      setLocalValueTo(finalValueTo)
    }

    const nextFilters: TransactionsFilters = {
      ...appliedFiltersRef.current,
      valueFrom: finalValueFrom,
      valueTo: finalValueTo,
    }

    if (
      appliedFiltersRef.current.valueFrom === finalValueFrom &&
      appliedFiltersRef.current.valueTo === finalValueTo
    )
      return

    applyFilters(nextFilters)
  }

  const handleClearFilters = () => {
    const emptyFilters: TransactionsFilters = {
      categoryIds: [],
      type: '',
      dateFrom: '',
      dateTo: '',
      valueFrom: undefined,
      valueTo: undefined,
    }

    setLocalCategoryIds([])
    setLocalType('')
    setLocalDateFrom('')
    setLocalDateTo('')
    setLocalValueFrom(undefined)
    setLocalValueTo(undefined)

    applyFilters(emptyFilters)

    const params = new URLSearchParams(searchParams)
    params.delete('categoriesIds')
    setSearchParams(params, { replace: true })
  }

  return {
    isDirty,
    appliedFiltersRef,

    localCategoryIds,
    setLocalCategoryIds,
    handleCategoryIdsChange,
    handleApplyCategories,
    handleRemoveCategoryId,

    localType,
    setLocalType,
    handleTypeChange,
    handleApplyType,

    localDateFrom,
    localDateTo,
    setLocalDateFrom,
    setLocalDateTo,
    handleDateFromChange,
    handleDateToChange,
    handleApplyDates,

    localValueFrom,
    localValueTo,
    setLocalValueFrom,
    setLocalValueTo,
    handleValueFromChange,
    handleValueToChange,
    handleApplyValues,

    handleClearFilters,
  }
}
