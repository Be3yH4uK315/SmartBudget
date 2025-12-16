import { SliceCaseReducers } from '@shared/types/reduxToolkit'
import { CurrentGoal } from './goals'

export type CurrentGoalSliceState = {
  goal: CurrentGoal
  isLoading: boolean

  isEditLoading: boolean
}

export type CurrentGoalSliceReducers = SliceCaseReducers<CurrentGoalSliceState>
