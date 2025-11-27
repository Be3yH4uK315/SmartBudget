type dashboardSliceState = {
    goals: DashboardGoal[]

    categories: DashboardCategory[]

    budgetTotalLimit: number

    isLoading: boolean
}

type dashboardSliceReducers = SliceCaseReducers<dashboardSliceState>
