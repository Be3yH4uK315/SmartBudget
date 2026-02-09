import { TransactionType } from '@features/transactions/types'

const rubFormatter = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  minimumFractionDigits: 0,
})

export function formatCurrency(value: number | string, type?: TransactionType): string {
  const num = typeof value === 'string' ? Number(value) : value

  if (Number.isNaN(num)) return '—'

  const prefix = type === 'income' ? '+ ' : type === 'expense' ? '- ' : ''
  return `${prefix}${rubFormatter.format(num)}`
}
