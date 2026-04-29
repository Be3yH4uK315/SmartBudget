import { Goal } from '@features/goals/types'

export const STATUS_PRIORITY: Record<Goal['status'], number> = {
  ongoing: 0,
  expired: 1,
  achieved: 2,
  closed: 3,
}
