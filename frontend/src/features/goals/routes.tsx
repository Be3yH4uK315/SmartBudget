import { lazy } from 'react'
import { SuspenseFallbackWrapper } from '@shared/components'
import { Route } from 'react-router'
import { CurrentGoalScreenSkeleton } from './screens/CurrentGoalScreen'
import { GoalsScreenSkeleton } from './screens/GoalsScreen'

const GoalsScreen = lazy(() => import('./screens/GoalsScreen/GoalsScreen'))
const GoalScreen = lazy(() => import('./screens/CurrentGoalScreen/CurrentGoalScreen'))

export const goalsRoutes = {
  pages: (
    <Route path="goals">
      <Route
        index
        element={
          <SuspenseFallbackWrapper Fallback={<GoalsScreenSkeleton />}>
            <GoalsScreen />
          </SuspenseFallbackWrapper>
        }
      />

      <Route
        path=":id"
        element={
          <SuspenseFallbackWrapper Fallback={<CurrentGoalScreenSkeleton />}>
            <GoalScreen />
          </SuspenseFallbackWrapper>
        }
      />
    </Route>
  ),
}
