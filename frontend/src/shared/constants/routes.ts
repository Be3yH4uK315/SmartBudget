export const ROUTES = {
  PAGES: {
    PUBLIC_PAGE: '/',
    TRANSACTIONS: '/transactions',
    GOALS: {
      MAIN: '/goals',
      ARCHIVE: '/goals/archive',
    },
    DASHBOARD: '/main',
    SETTINGS: {
      MAIN: '/settings',
      SECURITY: '/settings/security',
      BUDGET: '/settings/budget',
      NOTIFICATIONS: '/settings/notifications',
      SUPPORT: '/settings/support',
    },
    BUDGET: '/budget',
    LOGIN: '/auth/sign-in',
    RESET_PASSWORD: '/auth/reset-password',
    REGISTRATION: '/auth/registration',
  },
  GO_BACK: '../',
}

export const PUBLIC_ROUTES = [
  ROUTES.PAGES.LOGIN,
  ROUTES.PAGES.REGISTRATION,
  ROUTES.PAGES.RESET_PASSWORD,
  ROUTES.PAGES.PUBLIC_PAGE,
]
