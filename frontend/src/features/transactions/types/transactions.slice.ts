import { PayloadAction, SliceCaseReducers } from '@shared/types'
import { Category, TransactionsBlock, TransactionsFilters, TransactionType } from './transactions'

export type TransactionsSliceState = {
  transactions: TransactionsBlock[]
  isLoading: boolean

  filters: TransactionsFilters

  offset: number
  isLast: boolean
}

export type TransactionsSliceReducers = SliceCaseReducers<TransactionsSliceState> & {
  clearTransactionsState(state: TransactionsSliceState): void
  resetFilters(state: TransactionsSliceState): void
  setCategoryIds(state: TransactionsSliceState, action: PayloadAction<Category[]>): void
  setType(state: TransactionsSliceState, action: PayloadAction<TransactionType | ''>): void
  setDateFrom(state: TransactionsSliceState, action: PayloadAction<string>): void
  setDateTo(state: TransactionsSliceState, action: PayloadAction<string>): void
  setValueFrom(state: TransactionsSliceState, action: PayloadAction<number | undefined>): void
  setValueTo(state: TransactionsSliceState, action: PayloadAction<number | undefined>): void
}
