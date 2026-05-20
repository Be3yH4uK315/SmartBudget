import { LocaleDictionary } from '@shared/types/locale'

export const publicPageDict: LocaleDictionary = {
  ru: {
    PublicPage: {
      loginButton: 'Войти / Зарегистрироваться',
      headerTitle: 'Умный бюджет',
      heroTitle: 'Контролируй финансы — без усилий',
      heroSubtitle:
        'Умный бюджет автоматически распределяет расходы по категориям, следит за лимитами и помогает копить на цели.',
      heroCta: 'Начать бесплатно',
      featuresTitle: 'Всё необходимое в одном месте',
      howItWorks: 'Как это работает',
      ctaTitle: 'Готовы взять финансы под контроль?',
      ctaButton: 'Создать аккаунт',

      Feature: {
        One: {
          title: 'Умный бюджет',
          subtitle:
            'Задайте категории и лимиты. Приложение покажет, сколько осталось потратить в каждой категории.',
        },

        Two: {
          title: 'Авто-классификация',
          subtitle:
            'Транзакции определяются автоматически по мерчанту и коду MCC. Можно переопределить вручную.',
        },

        Three: {
          title: 'Цели-накопления',
          subtitle:
            'Ставьте финансовые цели с дедлайном — приложение рассчитает рекомендуемый ежемесячный взнос.',
        },

        Four: {
          title: 'Алерты и уведомления',
          subtitle:
            'Push-уведомление при достижении 80% и 100% лимита. Центр уведомлений всегда под рукой.',
        },
      },

      Steps: {
        First: {
          step: 'Шаг первый',
          title: 'Настройте бюджет',
          subtitle: 'Создайте категории и распределите доход по процентам или суммам',
        },

        Second: {
          step: 'Шаг второй',
          title: 'Подключите транзакции',
          subtitle: 'Сервис автоматически импортирует и классифицирует операции из банка.',
        },

        Third: {
          step: 'Шаг третий',
          title: 'Следите за прогрессом',
          subtitle: 'Дашборд «факт vs план» покажет отклонения и поможет не выйти за рамки.',
        },

        Fourth: {
          title: 'Готово!',
        },
      },
    },
  },

  en: {
    PublicPage: {
      loginButton: 'Log In / Sign Up',
      headerTitle: 'Smart Budget',
      heroTitle: 'Take Control of Your Finances — Effortlessly',
      heroSubtitle:
        'Smart Budget automatically categorizes your expenses, tracks spending limits, and helps you save toward your goals.',
      heroCta: 'Get Started for Free',
      featuresTitle: 'Everything You Need in One Place',
      howItWorks: 'How It Works',
      ctaTitle: 'Ready to Take Control of Your Finances?',
      ctaButton: 'Create Account',

      Feature: {
        One: {
          title: 'Smart Budget',
          subtitle:
            'Set up categories and spending limits. The app shows how much you still have available in each category.',
        },

        Two: {
          title: 'Automatic Categorization',
          subtitle:
            'Transactions are identified automatically using merchant names and MCC codes. You can always override them manually.',
        },

        Three: {
          title: 'Savings Goals',
          subtitle:
            'Set financial goals with deadlines — the app calculates the recommended monthly contribution.',
        },

        Four: {
          title: 'Alerts and Notifications',
          subtitle:
            'Receive push notifications when you reach 80% and 100% of your spending limits. The notification center is always within reach.',
        },
      },

      Steps: {
        First: {
          step: 'Step One',
          title: 'Set Up Your Budget',
          subtitle: 'Create categories and allocate your income by percentages or fixed amounts.',
        },

        Second: {
          step: 'Step Two',
          title: 'Connect Your Transactions',
          subtitle:
            'The service automatically imports and categorizes transactions from your bank.',
        },

        Third: {
          step: 'Step Three',
          title: 'Track Your Progress',
          subtitle:
            'The "Actual vs Plan" dashboard highlights deviations and helps you stay within budget.',
        },

        Fourth: {
          title: 'Done!',
        },
      },
    },
  },
}
