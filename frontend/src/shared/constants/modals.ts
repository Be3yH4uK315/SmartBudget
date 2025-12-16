import {
  ChangeCategoryModal,
  TransactionInfoModal,
} from '@features/transactions/screens/TransactionModal'
import { GoalModal } from 'src/features/goals/screens/GoalsModal/CreateGoalModal'

export const MODALS_MAP: Record<string, React.ComponentType<any>> = {
  transactionInfo: TransactionInfoModal,
  changeTransactionCategory: ChangeCategoryModal,
  createGoalModal: GoalModal,
}

export const MODAL_IDS = {
  TRANSACTION_INFO_MODAL: 'transactionInfo',
  CHANGE_CATEGORY_MODAL: 'changeTransactionCategory',
  CREATE_GOAL: 'createGoalModal',
}
