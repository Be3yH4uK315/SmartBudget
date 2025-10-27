export const selectUserName = (state: RootState) => {
  return state.user.name
}

export const selectUserEmail = (state: RootState) => {
  return state.user.email
}

export const selectUserRole = (state: RootState) => {
  return state.user.role
}

export const selectUserId = (state: RootState) => {
  return state.user.userId
}
