export function getDashboardInitialState(): dashboardSliceState {
  return {
    goals: [],
    categories: [],
    budgetLimit: 0,
    isLoading: true,
  }
}
