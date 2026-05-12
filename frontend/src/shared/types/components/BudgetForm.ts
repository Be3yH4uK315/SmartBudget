export type CategoryRow = {
  categoryId: number
  limitAmount?: number
  percent?: number
  mode?: 'amount' | 'percent'
}

export type FormValues = {
  totalLimitAmount: number | null
  isAutoRenew: boolean
  categories: CategoryRow[]
}
