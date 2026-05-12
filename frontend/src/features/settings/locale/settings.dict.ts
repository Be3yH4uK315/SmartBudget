import { LocaleDictionary } from '@shared/types'

export const settingsDict: LocaleDictionary = {
  ru: {
    Settings: {
      title: 'Настройки',

      Menu: {
        Security: {
          title: 'Безопасность',
          subtitle: 'Пароль и активные сессии',
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
          title: 'Смена пароля',
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

        RefreshDuration: {
          title: 'Автоматически завершать сессию',
          subtitle: 'Если сессия не активна:',
          week: 'Неделю',
          oneMonth: '1 месяц',
          threeMonth: '3 месяца',
          sixMonth: '6 месяцев',
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

      Budget: {
        title: 'Настройка бюджета',
        submitButton: 'Сохранить изменения',

        Month: {
          next: 'Бюджет на следующий месяц',
          current: 'Бюджет на текущий месяц',
        },

        Tooltip: {
          info: 'Вы можете либо настроить текущий бюджет, либо заранее задать бюджет на следующий месяц.',
          extraInfo:
            'Опция настройки бюджета на следующий месяц становится доступной с 25-го числа текущего месяца.',
        },

        MonthSwitch: {
          current: 'Текущий',
          next: 'Следующий',
        },
      },

      Notifications: {
        title: 'Настройки уведомлений',
        notificationsStatus: {
          title: 'Допуск уведомлений',
          subtitle: 'Разрешить отправку уведомлений (Отображаются в разделе "Уведомления")',
        },

        pushNotifications: {
          title: 'Push-уведомления',
          subtitle: 'Разрешить отправку push-уведомлений',
        },

        goals: {
          title: 'Цели',
          subtitle: 'Уведомлять о достижении цели, дедлайнах, и прочих действиях',
        },

        transactions: {
          title: 'Операции',
          subtitle:
            'Уведомлять о смене категорий, обнаружении неклассифицированных операциях и т.д.',
        },

        budget: {
          title: 'Бюджет и категории',
          totalLimit: 'Уведомлять о превышении лимита бюджета',
          categoriesLimit: 'Уведомлять о превышении лимита категорий',
        },
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

        Notifications: {
          title: 'Notifications',
          subtitle: 'Reaching category limits, goals, and more',
        },

        Budget: {
          title: 'Budget',
          subtitle: 'Budget and category limits',
        },
      },

      Security: {
        ChangePassword: {
          title: 'Change Password',
          oldPassword: 'Old Password',
          newPassword: 'New Password',
          newPasswordConfirm: 'Confirm New Password',
          button: 'Change Password',
          forgotPassword: 'Forgot Old Password',

          Errors: {
            tooShortPassword: 'Password must be at least 8 characters long',
            confirmPassword: 'Confirm password',
            passwordsNotMatch: "Passwords don't match",
          },
        },

        RefreshDuration: {
          title: 'Automatic Logout',
          subtitle: 'If session is inactive:',
          week: 'One Week',
          oneMonth: '1 Month',
          threeMonth: '3 Months',
          sixMonth: '6 Months',
        },

        Sessions: {
          title: 'Active Sessions',
          current: 'Current Session',
          deleteSession: 'End Session',
          lastActivity: 'Last activity: {{date}} at {{time}}',
        },

        title: 'Security Settings',
        deleteOtherSessions: 'End Other Sessions',
      },

      Budget: {
        title: 'Budget Settings',
        submitButton: 'Save Changes',

        Month: {
          next: 'Next Month Budget',
          current: 'Current Month Budget',
        },

        Tooltip: {
          info: 'You can either configure the current budget or set up the next month in advance.',
          extraInfo:
            'The option to set up the next month’s budget becomes available from the 25th of the current month.',
        },

        MonthSwitch: {
          current: 'Current',
          next: 'Next',
        },
      },

      Notifications: {
        title: 'Notification Settings',
        notificationsStatus: {
          title: 'Allow Notifications',
          subtitle: 'Enable notifications (Shown in the "Notifications" section)',
        },

        pushNotifications: {
          title: 'Push Notifications',
          subtitle: 'Allow sending push notifications',
        },

        goals: {
          title: 'Goals',
          subtitle: 'Notify about goal achievements, deadlines, and other actions',
        },

        transactions: {
          title: 'Transactions',
          subtitle: 'Notify about category changes, uncategorized transactions, etc.',
        },

        budget: {
          title: 'Budget and Categories',
          totalLimit: 'Notify when budget limit is exceeded',
          categoriesLimit: 'Notify when category limits are exceeded',
        },
      },
    },
  },
}
