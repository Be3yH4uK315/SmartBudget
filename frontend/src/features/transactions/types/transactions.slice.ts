import { SliceCaseReducers } from '@shared/types/reduxToolkit'
import { TransactionsBlock } from './transactions'

export type TransactionsSliceState = {
  transactions: TransactionsBlock[]
  isLoading: boolean

  offset: number
  isLast: boolean
}

export type TransactionsSliceReducers = SliceCaseReducers<TransactionsSliceState>
