import { TransactionStatus, TransactionType } from '@features/transactions/types'

export const TYPES: TransactionType[] = ['expense', 'income']
export const STATUSES: TransactionStatus[] = ['confirmed', 'rejected', 'pending']
