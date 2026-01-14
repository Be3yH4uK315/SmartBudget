export type CenterLabel =
  | {
      type: 'percent'
      value: number
    }
  | {
      type: 'amount'
      total: number
      label?: string
    }

export type PieDataItem = {
  value: number
  label?: string
  color?: string
  lightColor?: string
}

export type FilterType = 'income' | 'expense'

export type TransactionBase = {
  value: number
  type: FilterType
  categoryId?: number
  month?: number
}
