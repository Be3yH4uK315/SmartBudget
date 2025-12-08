type DashboardSliceState = {
  goals: DashboardGoal[]

  categories: DashboardCategory[]

  budgetLimit: number

  isLoading: boolean
}

type DashboardSliceReducers = SliceCaseReducers<DashboardSliceState>
