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
  categoryId: Category
  /** Описание */
  description: string | null
  /** Продавец / название */
  merchant: string
  /** МСС */
  mcc: string | null
  /** Статус */
  status: 'confirmed' | 'rejected' | 'pending'
  /** Дата транзакции */
  date: string
  /** Тип транзакции */
  transactionType: TransactionType
}

export type TransactionType = 'income' | 'expense'

export type ChangeCategoryRequest = {
  transactionId: string
  categoryId: Category
}

export type TransactionsBlock = {
  date: string
  items: Transaction[]
}

export type TransactionsFilters = {
  categoryIds: Category[]
  valueFrom?: number
  valueTo?: number
  dateFrom: string
  dateTo: string
  type: TransactionType | ''
}

export type Category = (typeof CATEGORY_IDS)[number]

export type TransactionsChip =
  | { type: 'category'; id: number }
  | { type: 'date'; from?: string; to?: string }
  | { type: 'value'; from?: number; to?: number }
  | { type: 'type'; value: string }
