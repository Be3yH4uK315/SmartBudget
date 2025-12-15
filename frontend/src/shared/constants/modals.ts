import {
  ChangeCategoryModal,
  TransactionInfoModal,
} from '@features/transactions/screens/TransactionModal'

export const MODALS_MAP: Record<string, React.ComponentType<any>> = {
  transactionInfo: TransactionInfoModal,
  changeTransactionCategory: ChangeCategoryModal,
}
