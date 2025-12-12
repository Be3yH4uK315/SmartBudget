export type TransactionsApiRequestPayload = {
  /** Временно для тестов */
  userId: string
  /** Кол-во строк */
  limit: number
  /** Сколько всего строк получил */
  offset: number
}

export type Transaction = {
  transactionId: string
  /** Сумма */
  value: number
  /** ID категории */
  categoryId: number
  /** Описание */
  description: string | null
  /** Продавец / название */
  name: string | null
  /** МСС */
  mcc: string | null
  /** Статус */
  status: 'confirmed' | 'rejected' | 'pending'
  /** Дата транзакции */
  date: string
  /** Тип транзакции */
  type: 'income' | 'expense'
}

export type ChangeCategoryRequest = {
  transactionId: string
  categoryId: number
}

export type TransactionsBlock = {
  date: string
  transactions: Transaction[]
}

export type TempAddPayload = {
  /** Временно для тестов */
  userId: string

  accountId: string

  value: number

  categoryId: number

  description: string

  name: string
}
