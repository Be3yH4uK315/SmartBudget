import { SliceCaseReducers } from "@reduxjs/toolkit"
import { DashboardGoal, DashboardCategory } from "./dashboard"

export type DashboardSliceState = {
  goals: DashboardGoal[]

  categories: DashboardCategory[]

  budgetLimit: number

  isLoading: boolean
}

export type DashboardSliceReducers = SliceCaseReducers<DashboardSliceState>
