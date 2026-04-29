export type CategoryRow = {
  categoryId: number
  limit?: number
  percent?: number
  mode?: 'amount' | 'percent'
}

export type FormValues = {
  totalLimit: number | null
  isAutoRenew: boolean
  categories: CategoryRow[]
}
