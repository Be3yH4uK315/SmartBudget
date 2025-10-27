import { ReactNode } from 'react'
import { BrowserRouter } from 'react-router'

interface Props {
  children: ReactNode
}

export function RouterProvider({ children }: Props) {
  return <BrowserRouter>{children}</BrowserRouter>
}
