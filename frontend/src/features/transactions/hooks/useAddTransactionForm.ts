import { useState } from 'react'
import { SelectChangeEvent } from '@mui/material'
import { Dayjs } from 'dayjs'
import { CategoryNumber, TransactionStatus, TransactionType } from '../types'

type ManualTransactionForm = {
  accountId?: string
  amount: number | ''
  transactionType: TransactionType | undefined
  date?: string
  categoryId: CategoryNumber | undefined
  description: string | undefined
  merchant: string
  mcc: number | undefined
  status: TransactionStatus | undefined
}

export function useAddTransactionForm() {
  const initialValues: ManualTransactionForm = {
    accountId: undefined,
    amount: '',
    transactionType: undefined,
    date: undefined,
    categoryId: undefined,
    description: undefined,
    merchant: '',
    mcc: undefined,
    status: undefined,
  }

  const [values, setValues] = useState<ManualTransactionForm>(initialValues)

  const handleChange =
    <K extends keyof Omit<ManualTransactionForm, 'transactionType' | 'status'>>(key: K) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value

      setValues((prev) => ({
        ...prev,
        [key]:
          key === 'amount' || key === 'mcc'
            ? value === '' || Number.isNaN(Number(value))
              ? ''
              : Number(value)
            : value,
      }))
    }

  const handleDateChange = (newValue: Dayjs | null) => {
    setValues((prev) => ({
      ...prev,
      date: newValue ? newValue.format('YYYY-MM-DD') : undefined,
    }))
  }

  const handleCategoryChange = (event: SelectChangeEvent<CategoryNumber | undefined>) => {
    const value = event?.target?.value
    setValues((prev) => ({
      ...prev,
      categoryId: value ? (Number(value) as CategoryNumber) : undefined,
    }))
  }

  const handleGoalChange = (event: SelectChangeEvent<string | undefined>) => {
    const value = event?.target?.value
    setValues((prev) => ({
      ...prev,
      accountId: value ? value : undefined,
    }))
  }

  const setType = (type: TransactionType) => {
    setValues((prev) => ({
      ...prev,
      transactionType: prev.transactionType === type ? undefined : type,
    }))
  }

  const setStatus = (status: TransactionStatus) => {
    setValues((prev) => ({
      ...prev,
      status: prev.status === status ? undefined : status,
    }))
  }

  const canSubmit = () => {
    if (
      Number(values.amount) < 1 ||
      values.transactionType === undefined ||
      values.status === undefined ||
      values.merchant === ''
    )
      return false

    return true
  }

  const setPayload = () => ({
    accountId: values.accountId?.trim(),
    amount: Number(values.amount),
    transactionType: values.transactionType,
    date: values.date,
    categoryId: values.categoryId,
    description: values.description,
    merchant: values.merchant,
    mcc: values.mcc,
    status: values.status,
  })

  return {
    values,
    handleChange,
    handleDateChange,
    setType,
    setStatus,
    handleCategoryChange,
    handleGoalChange,
    canSubmit,
    setPayload,
  }
}
