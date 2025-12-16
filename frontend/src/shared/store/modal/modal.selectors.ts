import { RootState } from '@shared/types/store'
import { modalSlice } from './modal.slice'

export const selectModal = (state: RootState) => modalSlice.selectSlice(state)
