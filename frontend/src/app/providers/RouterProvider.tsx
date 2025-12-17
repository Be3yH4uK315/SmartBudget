import { ReactNode } from 'react'
import { BrowserRouter } from 'react-router'

interface Props {
  children: ReactNode
}

export const RouterProvider = ({ children }: Props) => {
  return <BrowserRouter>{children}</BrowserRouter>
}
