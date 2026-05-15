import { SliceCaseReducers } from '@reduxjs/toolkit'
import { DashboardCategory, DashboardGoal } from './dashboard'

export type DashboardSliceState = {
  goals: DashboardGoal[]

  categories: DashboardCategory[]

  budgetLimit: number

  isGoalsLoading: boolean

  isBudgetLoading: boolean
}

export type DashboardSliceReducers = SliceCaseReducers<DashboardSliceState> & {
  clearDashboardState(state: DashboardSliceState): void
}
