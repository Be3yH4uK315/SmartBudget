import { createSlice } from '@reduxjs/toolkit'
import { ModalSliceReducers, ModalSliceState } from '@shared/types'
import { getModalInitialState } from './modal.state'

export const modalSlice = createSlice<ModalSliceState, ModalSliceReducers, 'modal', any>({
  name: 'modal',
  initialState: getModalInitialState(),
  reducers: {
    openModal(state, { payload }) {
      state.id = payload.id
      state.props = payload.props
    },

    closeModal(state) {
      state.id = null
      state.props = undefined
    },
  },
})

export const modalReducer = modalSlice.reducer
export const { openModal, closeModal } = modalSlice.actions
