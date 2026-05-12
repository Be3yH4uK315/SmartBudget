import { LocaleDictionary } from '@shared/types'

export const budgetFormDict: LocaleDictionary = {
  ru: {
    BudgetForm: {
      EmptyList: {
        title: 'Лимиты не установлены',
        subtitle: 'Вы можете добавить категорию и установить лимит, используя кнопку ниже',
      },

      CategoriesLimits: {
        title: 'Лимиты по категориям',
        tooltip:
          'Если установлен лимит бюджета, сумма процентных лимитов по категориям не может быть больше 100%',

        percentOverflow: 'Лимиты по категориям превышают лимит бюджета на {{value}}',
        remainingPercent: 'Осталось распределить {{value}} бюджета',

        CategoryCard: {
          percentHelperText: 'Процент от бюджета',
          percentLabel: 'Процент',

          valueHelperText: 'Лимит по сумме',
          valueLabel: 'Сумма',
        },

        AddCategoryCard: {
          newCategory: 'Добавление категории',
          addCategoryButton: 'Добавить категорию',
          cancelButton: 'Отменить',
          placeholder: 'Категория',
        },
      },

      BudgetLimit: {
        title: 'Лимит бюджета',
        subtitle: 'Запланируйте максимальную сумму трат для вашего бюджета',
        valueLabel: 'Сумма',
        tooltip:
          'При установке лимита бюджета вы можете задать лимиты категорий в процентах от общего лимита',
      },

      AutoRenew: {
        title: 'Автопродление бюджета',
        subtitle: 'Автоматически настраивать новый бюджет в начале месяца',
        tooltip: 'Автоматически формирует бюджет на следующий месяц по образцу текущего',
      },
    },
  },
  en: {
    BudgetForm: {
      EmptyList: {
        title: 'No limits set',
        subtitle: 'You can add a category and set a limit using the button below',
      },

      CategoriesLimits: {
        title: 'Category limits',
        tooltip:
          'If a budget limit is set, the total percentage of category limits cannot exceed 100%',

        percentOverflow: 'Category limits exceed the budget limit by {{value}}',
        remainingPercent: '{{value}} of the budget left to allocate',

        CategoryCard: {
          percentHelperText: 'Percentage of the budget',
          percentLabel: 'Percentage',

          valueHelperText: 'Amount limit',
          valueLabel: 'Amount',
        },

        AddCategoryCard: {
          newCategory: 'Add category',
          addCategoryButton: 'Add category',
          cancelButton: 'Cancel',
          placeholder: 'Category',
        },
      },

      BudgetLimit: {
        title: 'Budget limit',
        subtitle: 'Plan the maximum amount of spending for your budget',
        valueLabel: 'Amount',
        tooltip:
          'When setting a budget limit, you can define category limits as a percentage of the total limit',
      },

      AutoRenew: {
        title: 'Auto-renew budget',
        subtitle: 'Automatically set up a new budget at the beginning of the month',
        tooltip: 'Automatically creates the next month’s budget based on the current one',
      },
    },
  },
}
