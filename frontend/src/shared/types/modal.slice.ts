import { SliceCaseReducers } from '@reduxjs/toolkit'
import { PayloadAction } from './reduxToolkit'

export type ModalSliceState = {
  id: string | null
  props?: Record<string, any>
}

export type ModalSliceReducers = SliceCaseReducers<ModalSliceState> & {
  openModal(
    state: ModalSliceState,
    action: PayloadAction<{ id: string; props?: Record<string, any> }>,
  ): void

  closeModal(state: ModalSliceState): void
}
