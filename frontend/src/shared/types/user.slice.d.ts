type userSliceState = {
  userId: string
  role: 0 | 1
  name: string
  email: string
}

type userSliceReducers = SliceCaseReducers<userSliceState>
