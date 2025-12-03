type dashboardSliceState = {
  goals: DashboardGoal[]

  categories: DashboardCategory[]

  budgetLimit: number

  isLoading: boolean
}

type dashboardSliceReducers = SliceCaseReducers<dashboardSliceState>
