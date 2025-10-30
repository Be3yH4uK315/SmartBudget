import { ReactNode } from 'react'
import { store } from '@shared/store/store'
import { Provider } from 'react-redux'

type Props = {
  children: ReactNode
}

export function ReduxProvider({ children }: Props) {
  return <Provider store={store}>{children}</Provider>
}
