import { CATEGORY_IDS } from '@shared/constants'

export type TransactionsApiRequestPayload = {
  /** Кол-во строк */
  limit: number
  /** Сколько всего строк получил */
  offset: number
}

export type Transaction = {
  transactionId: string
  /** Сумма */
  amount: number
  /** ID категории */
  categoryId: CategoryNumber
  /** Описание */
  description: string | null
  /** Продавец / название */
  merchant: string
  /** МСС */
  mcc: string | null
  /** Статус */
  status: TransactionStatus
  /** Дата транзакции */
  date: string
  /** Тип транзакции */
  transactionType: TransactionType
}

export type TransactionStatus = 'confirmed' | 'rejected' | 'pending'

export type TransactionType = 'income' | 'expense'

export type ChangeCategoryRequest = {
  transactionId: string
  categoryId: CategoryNumber
}

export type TransactionsBlock = {
  date: string
  items: Transaction[]
}

export type TransactionsFilters = {
  categoryIds: CategoryNumber[]
  valueFrom?: number
  valueTo?: number
  dateFrom: string
  dateTo: string
  type: TransactionType | ''
}

export type CategoryNumber = (typeof CATEGORY_IDS)[number]

export type TransactionsChip =
  | { type: 'category'; id: number }
  | { type: 'date'; from?: string; to?: string }
  | { type: 'value'; from?: number; to?: number }
  | { type: 'type'; value: string }

export type ManualTransaction = {
  accountId?: string

  amount: number

  transactionType?: TransactionType

  date?: string

  categoryId?: CategoryNumber

  description?: string

  merchant: string

  mcc?: number

  status?: TransactionStatus
}

export type GoalId = {
  goalId: string
  name: string
}
