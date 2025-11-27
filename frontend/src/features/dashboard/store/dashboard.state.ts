export function getDashboardInitialState(): dashboardSliceState {
  return {
    goals: [],
    categories: [],
    budgetTotalLimit: 0,
    isLoading: true
  }
}
