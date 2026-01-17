import { LocaleDictionary } from '@shared/types'

export const settingsDict: LocaleDictionary = {
  ru: {
    Settings: {
      title: 'Настройки',

      RefreshDuration: {
        title: 'Автоматически завершать сессию',
        subtitle: 'Если сессия не активна:',
        week: 'Неделю',
        oneMonth: '1 месяц',
        threeMonth: '3 месяца',
        sixMonth: '6 месяцев',
      },

      Menu: {
        Security: {
          title: 'Безопасность',
          subtitle: 'Пароль и активные сессии',
        },

        Support: {
          title: 'Обращения',
          subtitle: 'Ваши обращения в поддержку',
        },

        Notifications: {
          title: 'Уведомления',
          subtitle: 'Достижение лимитов, целей и другие',
        },

        Budget: {
          title: 'Бюджет',
          subtitle: 'Лимиты по категориям и бюджет',
        },
      },

      Security: {
        ChangePassword: {
          title: 'Cмена пароля',
          oldPassword: 'Старый пароль',
          newPassword: 'Новый пароль',
          newPasswordConfirm: 'Повторите новый пароль',
          button: 'Сменить пароль',
          forgotPassword: 'Забыл старый пароль',

          Errors: {
            tooShortPassword: 'Пароль должен содержать минимум 8 символов',
            confirmPassword: 'Подтвердите пароль',
            passwordsNotMatch: 'Пароли не совпадают',
          },
        },

        Sessions: {
          title: 'Активные сессии',
          current: 'Текущая сессия',
          deleteSession: 'Завершить',
          lastActivity: 'Последняя активность: {{date}} в {{time}}',
        },

        title: 'Настройки безопасности',
        deleteOtherSessions: 'Завершить другие сессии',
      },
    },
  },

  en: {
    Settings: {
      title: 'Settings',

      Menu: {
        Security: {
          title: 'Security',
          subtitle: 'Password and active sessions',
        },

        Support: {
          title: 'Support',
          subtitle: 'Your tickets',
        },

        Notifications: {
          title: 'Notifications',
          subtitle: 'Reaching categories limits, goals etc.',
        },

        Budget: {
          title: 'Budget',
          subtitle: 'Budget and categories limits',
        },
      },

      Security: {
        ChangePassword: {
          title: 'Change password',
          oldPassword: 'Old password',
          newPassword: 'New password',
          newPasswordConfirm: 'Confirm new password',
          button: 'Change password',
          forgotPassword: 'Forgot old password',

          Errors: {
            tooShortPassword: 'The password must contain at least 8 characters',
            confirmPassword: 'Confirm password',
            passwordsNotMatch: "The passwords don't match",
          },
        },

        Sessions: {
          title: 'Active sessions',
          current: 'Current session',
          deleteSession: 'Revoke',
          lastActivity: 'Last activity: {{date}} at {{time}}',
        },

        title: 'Security settings',
        deleteOtherSessions: 'Revoke other sessions',
      },
    },
  },
}
