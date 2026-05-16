import { LocaleDictionary } from '@shared/types'

export const toastsDict: LocaleDictionary = {
  ru: {
    Toasts: {
      error: 'Произошла ошибка',
      success: 'Готово',
      message: {
        cannotGetBudgetData: 'Не удалось загрузить данные бюджета',
        cannotCreateBudget: 'Не удалось создать бюджет',

        cannotGetGoal: 'Не удалось загрузить информацию о цели',
        cannotGetGoalTransactions: 'Не удалось загрузить операции по цели',
        cannotEditGoal: 'Не удалось сохранить изменения цели',
        cannotUpdateGoalStatus: 'Не удалось изменить статус цели',
        cannotUpdateArchivedStatus: 'Не удалось изменить статус архивации цели',
        cannotGetGoals: 'Не удалось загрузить список целей',
        cannotCreateGoal: 'Не удалось создать цель',

        cannotGetNotifications: 'Не удалось загрузить уведомления',
        cannotMarkAsRead: 'Не удалось отметить уведомление как прочитанное',
        cannotMarkAllAsRead: 'Не удалось отметить все уведомления как прочитанные',

        cannotSubmitForm: 'Проверьте корректность заполнения формы',

        cannotEnablePushNotifications: 'Не удалось включить push-уведомления',

        cannotGetBudgetSettings: 'Не удалось загрузить настройки бюджета',
        cannotSetBudgetSettings: 'Не удалось сохранить настройки бюджета',

        cannotGetNotificationsSettings: 'Не удалось загрузить настройки уведомлений',
        cannotChangeNotificationsStatus: 'Не удалось изменить статус уведомлений',
        cannotUpdateNotificationsSettings: 'Не удалось сохранить настройки уведомлений',

        cannotGetSessions: 'Не удалось загрузить список активных сессий',
        cannotDeleteSession: 'Не удалось завершить текущую сессию',
        cannotDeleteOtherSession: 'Не удалось завершить другие сессии',

        cannotChangePassword: 'Не удалось изменить пароль',
        cannotChangeRefreshTokenDuration: 'Не удалось изменить срок действия токена',
        cannotGetRefreshTokenDuration: 'Не удалось загрузить срок действия токена',

        cannotGetTransactions: 'Не удалось загрузить транзакции',
        cannotChangeCategory: 'Не удалось изменить категорию транзакции',
        cannotAddTransaction: 'Не удалось создать транзакцию',
        cannotImportTransaction: 'Не удалось импортировать транзакции',

        cannotGetGoalsNames: 'Не удалось загрузить список доступных целей',
        cannotSearch: 'Не удалось выполнить поиск',
        cannotUpdateLang: 'Не удалось изменить язык приложения',
        cannotGetUnreadCount: 'Не удалось загрузить количество непрочитанных уведомлений',

        noInfo: 'Ошибка при получении данных пользователя',

        budgetCreated: 'Бюджет успешно создан',
        goalEdited: 'Изменения цели сохранены',
        budgetSettingsSet: 'Настройки бюджета сохранены',
        notificationsSettingsUpdated: 'Настройки уведомлений сохранены',
        sessionDeleted: 'Сессия успешно завершена',
        passwordChanged: 'Пароль успешно изменён',
        refreshTokenDurationChanged: 'Срок действия токена обновлён',
        categoryChanged: 'Категория успешно изменена',
        transactionAdded: 'Транзакция успешно создана',
        transactionsImported: 'Транзакции успешно импортированы',
      },
    },
  },

  en: {
    Toasts: {
      error: 'Error',
      success: 'Success',
      message: {
        cannotGetBudgetData: 'Failed to load budget data',
        cannotCreateBudget: 'Failed to create budget',
        cannotGetGoal: 'Failed to load goal details',
        cannotGetGoalTransactions: 'Failed to load goal transactions',
        cannotEditGoal: 'Failed to save goal changes',
        cannotUpdateGoalStatus: 'Failed to update goal status',
        cannotUpdateArchivedStatus: 'Failed to update goal archive status',
        cannotGetGoals: 'Failed to load goals',
        cannotCreateGoal: 'Failed to create goal',
        cannotGetNotifications: 'Failed to load notifications',
        cannotMarkAsRead: 'Failed to mark notification as read',
        cannotMarkAllAsRead: 'Failed to mark all notifications as read',
        cannotSubmitForm: 'Please check the form fields',
        cannotEnablePushNotifications: 'Failed to enable push notifications',
        cannotGetBudgetSettings: 'Failed to load budget settings',
        cannotSetBudgetSettings: 'Failed to save budget settings',
        cannotGetNotificationsSettings: 'Failed to load notification settings',
        cannotChangeNotificationsStatus: 'Failed to update notification status',
        cannotUpdateNotificationsSettings: 'Failed to save notification settings',
        cannotGetSessions: 'Failed to load active sessions',
        cannotDeleteSession: 'Failed to end the current session',
        cannotDeleteOtherSession: 'Failed to end other sessions',
        cannotChangePassword: 'Failed to change password',
        cannotChangeRefreshTokenDuration: 'Failed to update token lifetime',
        cannotGetRefreshTokenDuration: 'Failed to load token lifetime',
        cannotGetTransactions: 'Failed to load transactions',
        cannotChangeCategory: 'Failed to change transaction category',
        cannotAddTransaction: 'Failed to create transaction',
        cannotImportTransaction: 'Failed to import transactions',
        cannotGetGoalsNames: 'Failed to load available goals',
        cannotSearch: 'Search failed',
        cannotUpdateLang: 'Failed to change application language',
        cannotGetUnreadCount: 'Failed to load unread notification count',
        noInfo: 'Failed to load user information',

        budgetCreated: 'Budget created successfully',
        goalEdited: 'Goal updated successfully',
        budgetSettingsSet: 'Budget settings saved successfully',
        notificationsSettingsUpdated: 'Notification settings saved successfully',
        sessionDeleted: 'Session ended successfully',
        passwordChanged: 'Password changed successfully',
        refreshTokenDurationChanged: 'Token lifetime updated successfully',
        categoryChanged: 'Category changed successfully',
        transactionAdded: 'Transaction created successfully',
        transactionsImported: 'Transactions imported successfully',
      },
    },
  },
}
