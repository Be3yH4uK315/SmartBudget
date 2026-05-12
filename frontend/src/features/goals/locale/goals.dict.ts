import { LocaleDictionary } from '@shared/types'

export const goalsDict: LocaleDictionary = {
  ru: {
    Goals: {
      NoGoals: {
        Empty: {
          Archive: {
            title: 'Архив пока пуст',
            subtitle: ' ',
          },

          title: 'Нет целей',
          subtitle: 'Здесь можно создать цель и копить на приятные мелочи',
        },

        Filtered: {
          Archive: {
            title: 'Кажется, таких целей нет',
            subtitle: 'Попробуйте убрать лишние фильтры',
          },

          title: 'Кажется, таких целей нет',
          subtitle: 'Попробуйте убрать лишние фильтры',
        },
      },

      title: 'Ваши цели',
      create: 'Создать цель',

      archiveTitle: 'Архив целей',
      goBack: 'Назад',

      Modal: {
        editTitle: 'Редактирование Цели',
        editButton: 'Сохранить изменения',

        createTitle: 'Создание цели',
        createButton: 'Создать цель',

        name: 'Название',
        value: 'Сумма',
        date: 'Дата окончания',

        priorityTags: 'Приоритет цели',
        otherTags: 'Прочие тэги',
      },

      Filters: {
        selected: 'Выбрано: {{value}}',
        placeholder: {
          tags: 'Тэги',
          priority: 'Приоритет',
        },
      },
      Tags: {
        clear: 'Сбросить фильтры',
        archive: 'Архив',

        High: 'Высокий приоритет',
        Medium: 'Средний приоритет',
        Low: 'Низкий Приоритет',
        Health: 'Здоровье',
        Education: 'Образование',
        Sport: 'Спорт',
        Travel: 'Путешествия',
        Home: 'Дом',
        Auto: 'Авто',
        Family: 'Семья',
        Presents: 'Подарки',
        Gadgets: 'Гаджеты',
        Charity: 'Благотворительность',
        RealEstate: 'Недвижимость',
        FinancialCushion: 'Подушка безопасности',
      },

      GoalsStats: {
        progress: 'Прогресс по всем целям',
        currentValue: 'Сумма накоплений по всем целям',
        targetValue: 'Осталось накопить',
      },

      GoalBlock: {
        currentValue: 'Накоплено: {{value}}',
        targetValue: 'Осталось: {{value}}',
        finishDate: 'Дата окончания: {{value}}',
      },

      CurrentGoal: {
        GoalStats: {
          daysLeft: 'До завершения цели',
          targetValue: 'Осталось накопить для достижения цели',

          nextPayment: 'Рекомендуем внести для завершения цели',
          nextPayment_one: 'Рекомендуем внести в течение {{count}} дня',
          nextPayment_few: 'Рекомендуем внести в течение {{count}} дней',
          nextPayment_many: 'Рекомендуем внести в течение {{count}} дней',

          day_one: '{{count}} день',
          day_few: '{{count}} дня',
          day_many: '{{count}} дней',
        },
      },
    },

    GoalStatus: {
      achieved: 'Достигнута',
      expired: 'Просрочена',
      closed: 'Закрыта',
      ongoing: 'В процессе',

      archived: 'В архиве',
    },

    CurrentGoal: {
      goBack: 'Назад',
      finishDate: 'Дата окончания: {{value}}',
      targetValue: 'Осталось накопить: {{value}}',

      Settings: {
        title: 'Настроить цель',
        subtitle: 'Редактировать название, сумму цели и дату окончания',
      },

      ActionsButtonsBlock: {
        buttonClose: 'Завершить цель',
        buttonRestore: 'Восстановить цель',

        archive: 'Переместить в архив',
        unarchive: 'Вернуть из архива',
      },

      TransactionsPieBlock: {
        title: 'Текущий результат',
        income: 'Пополнения',
        expense: 'Расходы',
      },

      TagsBlock: {
        title: 'Список тэгов',
        subtitle: 'Вы можете добавить или удалить тэги в настройках',
        noTagsSubtitle: 'Вы не установили тэги для этой цели',
        button: 'Установить тэги',
      },

      ProgressBlock: {
        title: 'Ваш прогресс по текущей цели',
        subtitle: 'Подключите автопополнение, чтобы достигать цели быстрее',
      },

      ExpiredBlock: {
        title: 'Цель просрочена',
        subtitle: 'Вы можете установить новую дату окончания цели в настройках',
      },
    },
  },

  en: {
    Goals: {
      NoGoals: {
        Empty: {
          Archive: {
            title: 'Archive is empty',
            subtitle: ' ',
          },

          title: 'No goals',
          subtitle: 'Here you can create a goal and save for something nice',
        },

        Filtered: {
          Archive: {
            title: 'No goals found',
            subtitle: 'Try removing some filters',
          },

          title: 'No goals found',
          subtitle: 'Try removing some filters',
        },
      },

      title: 'Your Goals',
      create: 'Create Goal',

      archiveTitle: 'Goals Archive',
      goBack: 'Back',

      Modal: {
        editTitle: 'Edit Goal',
        editButton: 'Save Changes',

        createTitle: 'Create Goal',
        createButton: 'Create Goal',

        name: 'Name',
        value: 'Amount',
        date: 'End Date',

        priorityTags: 'Goal Priority',
        otherTags: 'Other Tags',
      },

      Filters: {
        selected: 'Selected: {{value}}',
        placeholder: {
          tags: 'Tags',
          priority: 'Priority',
        },
      },

      Tags: {
        clear: 'Clear Filters',
        archive: 'Archive',

        High: 'High Priority',
        Medium: 'Medium Priority',
        Low: 'Low Priority',
        Health: 'Health',
        Education: 'Education',
        Sport: 'Sport',
        Travel: 'Travel',
        Home: 'Home',
        Auto: 'Car',
        Family: 'Family',
        Presents: 'Gifts',
        Gadgets: 'Gadgets',
        Charity: 'Charity',
        RealEstate: 'Real Estate',
        FinancialCushion: 'Emergency Fund',
      },

      GoalsStats: {
        progress: 'Progress on all goals',
        currentValue: 'Total savings for all goals',
        targetValue: 'Amount left to save',
      },

      GoalBlock: {
        currentValue: 'Saved: {{value}}',
        targetValue: 'Remaining: {{value}}',
        finishDate: 'End Date: {{value}}',
      },

      CurrentGoal: {
        GoalStats: {
          daysLeft: 'Days until goal completion',
          targetValue: 'Amount left to reach the goal',

          nextPayment: 'Recommended contribution to reach the goal',
          nextPayment_one: 'Recommended contribution within {{count}} day',
          nextPayment_few: 'Recommended contribution within {{count}} days',
          nextPayment_many: 'Recommended contribution within {{count}} days',

          day_one: '{{count}} day',
          day_few: '{{count}} days',
          day_many: '{{count}} days',
        },
      },
    },

    GoalStatus: {
      achieved: 'Achieved',
      expired: 'Expired',
      closed: 'Closed',
      ongoing: 'Ongoing',

      archived: 'Archived',
    },

    CurrentGoal: {
      goBack: 'Back',
      finishDate: 'End Date: {{value}}',
      targetValue: 'Remaining to save: {{value}}',

      Settings: {
        title: 'Configure Goal',
        subtitle: 'Edit name, target amount, and end date',
      },

      ActionsButtonsBlock: {
        buttonClose: 'Complete Goal',
        buttonRestore: 'Restore Goal',

        archive: 'Move to Archive',
        unarchive: 'Restore from Archive',
      },

      TransactionsPieBlock: {
        title: 'Current Result',
        income: 'Income',
        expense: 'Expenses',
      },

      TagsBlock: {
        title: 'Tags List',
        subtitle: 'You can add or remove tags in settings',
        noTagsSubtitle: 'No tags set for this goal',
        button: 'Set Tags',
      },

      ProgressBlock: {
        title: 'Your progress on this goal',
        subtitle: 'Enable auto-savings to reach the goal faster',
      },

      ExpiredBlock: {
        title: 'Goal Expired',
        subtitle: 'You can set a new end date in settings',
      },
    },
  },
}
