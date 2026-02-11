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
  en: {},
}
