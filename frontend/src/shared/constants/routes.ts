export const ROUTES = {
  PAGES: {
    PUBLIC_PAGE: '/',
    TRANSACTIONS: '/transactions',
    GOALS: '/goals',
    DASHBOARD: '/main',
    SETTINGS: '/settings',
    BUDGET_SETTINGS: '/settings/budget',
    BUDGET: '/budget',
    LOGIN: '/auth/sign-in',
    RESET_PASSWORD: '/auth/reset-password',
    REGISTRATION: '/auth/registration',
  },
}

export const PUBLIC_ROUTES = [
  ROUTES.PAGES.LOGIN,
  ROUTES.PAGES.REGISTRATION,
  ROUTES.PAGES.RESET_PASSWORD,
  ROUTES.PAGES.PUBLIC_PAGE,
]
