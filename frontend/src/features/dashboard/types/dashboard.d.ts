type DashboardResponsePayload = {
    goals: DashboardGoal[]

    categories: DashboardCategory[]

    budgetTotalLimit: number
}

type DashboardGoal = {
    name: string
    totalValue: number
    currentValue: number
}

type DashboardCategory = {
    categoryId: number
    value: number
}