import {
  ChangeCategoryModal,
  TransactionInfoModal,
} from '@features/transactions/screens/TransactionModal'

export const MODALS_MAP: Record<string, React.ComponentType<any>> = {
  transactionInfo: TransactionInfoModal,
  changeTransactionCategory: ChangeCategoryModal,
}

export const MODAL_IDS = {
  TRANSACTION_INFO_MODAL: 'transactionInfo',
  CHANGE_CATEGORY_MODAL: 'changeTransactionCategory',
}
