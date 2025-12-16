import { lazy } from 'react'
import { Route } from 'react-router'

const GoalsScreen = lazy(() => import('./screens/GoalsScreen/GoalsScreen'))
const GoalScreen = lazy(() => import('./screens/CurrentGoalScreen/CurrentGoalScreen'))

export const goalsRoutes = {
  pages: (
    <Route path="goals">
      <Route index element={<GoalsScreen />} /> {/** главная */}
      <Route path=":id" element={<GoalScreen />} /> {/** конкретная */}
    </Route>
  ),
}
