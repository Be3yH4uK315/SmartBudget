import { userSlice } from './user.slice'

export const selectUser = (state: RootState) => userSlice.selectSlice(state)
