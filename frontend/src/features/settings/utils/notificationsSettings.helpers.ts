import { NotificationsSettings, ServiceBlock } from '@features/settings/types'

export const mapSettingsToBlocks = (
  settings: Omit<NotificationsSettings, 'notificationsStatus'>,
  onChange: (path: string[], value: boolean) => void,
): ServiceBlock[] => {
  return [
    {
      title: 'email.title',
      options: [
        {
          title: 'email.subtitle',
          isChecked: settings.emailStatus,
          onClick: () => onChange(['emailStatus'], !settings.emailStatus),
        },
      ],
    },
    {
      title: 'goals.title',
      options: [
        {
          title: 'goals.subtitle',
          isChecked: settings.goals,
          onClick: () => onChange(['goals'], !settings.goals),
        },
      ],
    },
    {
      title: 'transactions.title',
      options: [
        {
          title: 'transactions.subtitle',
          isChecked: settings.transactions,
          onClick: () => onChange(['transactions'], !settings.transactions),
        },
      ],
    },
    {
      title: 'budget.title',
      options: [
        {
          title: 'budget.totalLimit',
          isChecked: settings.budget.totalLimit,
          onClick: () => onChange(['budget', 'totalLimit'], !settings.budget.totalLimit),
        },
        {
          title: 'budget.categoriesLimit',
          isChecked: settings.budget.categoriesLimit,
          onClick: () => onChange(['budget', 'categoriesLimit'], !settings.budget.categoriesLimit),
        },
      ],
    },
  ]
}

export function updateByPath<T>(obj: T, path: string[], value: boolean): T {
  const newObj = structuredClone(obj)

  let current: any = newObj

  for (let i = 0; i < path.length - 1; i++) {
    current = current[path[i]]
  }

  current[path[path.length - 1]] = value

  return newObj
}
