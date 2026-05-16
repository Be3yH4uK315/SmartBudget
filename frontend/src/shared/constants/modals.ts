import { CreateBudgetModal } from '@features/budget/screens/CreateBudgetModal'
import {
  AddTransactionModal,
  ChangeCategoryModal,
  TransactionInfoModal,
} from '@features/transactions/screens/TransactionModal'
import { GoalModal } from 'src/features/goals/screens/GoalsModal/CreateGoalModal'

export const MODALS_MAP: Record<string, React.ComponentType<any>> = {
  transactionInfo: TransactionInfoModal,
  addTransaction: AddTransactionModal,
  changeTransactionCategory: ChangeCategoryModal,
  createGoalModal: GoalModal,
  createBudgetModal: CreateBudgetModal,
}

export const MODAL_IDS = {
  TRANSACTION_INFO_MODAL: 'transactionInfo',
  TRANSACTION_ADD_MODAL: 'addTransaction',
  CHANGE_CATEGORY_MODAL: 'changeTransactionCategory',
  CREATE_GOAL: 'createGoalModal',
  CREATE_BUDGET: 'createBudgetModal',
}
