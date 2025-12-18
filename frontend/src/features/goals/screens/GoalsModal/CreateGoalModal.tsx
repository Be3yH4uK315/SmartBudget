import { useEffect, useState } from 'react'
import 'dayjs/locale/ru'
import { editGoal } from '@features/goals/store/currentGoal'
import { createGoal } from '@features/goals/store/goals'
import { CurrentGoal } from '@features/goals/types'
import { CloseOutlined } from '@mui/icons-material'
import { Button, IconButton, Stack, TextField, Typography } from '@mui/material'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { useTranslate } from '@shared/hooks'
import ModalLayout from '@shared/screens/ModalProvider'
import { dispatch } from '@shared/store'
import dayjs, { Dayjs } from 'dayjs'

type Props = {
  goal?: CurrentGoal
  onClose: () => void
}

type FormValues = {
  name: string
  targetValue: number | ''
  finishDate: string
}

export const GoalModal = ({ onClose, goal }: Props) => {
  const translate = useTranslate('Goals')
  const mode: 'create' | 'edit' = goal ? 'edit' : 'create'

  const [values, setValues] = useState<FormValues>({
    name: '',
    targetValue: '',
    finishDate: '',
  })

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setValues({
      name: goal?.name ?? '',
      targetValue: goal?.targetValue ?? '',
      finishDate: goal?.finishDate ?? '',
    })
  }, [goal])

  const handleChange =
    <K extends keyof FormValues>(key: K) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value

      setValues((prev) => ({
        ...prev,
        [key]: key === 'targetValue' ? (value === '' ? '' : Number(value)) : value,
      }))
    }

  const canSubmit = (): boolean => {
    const { name, targetValue, finishDate } = values

    if (!name.trim() || targetValue === '' || !finishDate) return false

    const today = new Date()
    const finish = new Date(finishDate)
    if (finish < new Date(today.toDateString())) return false

    return true
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (values.targetValue === '') {
      return
    }

    const payload = {
      name: values.name,
      targetValue: values.targetValue,
      finishDate: values.finishDate,
    }

    if (mode === 'create') {
      dispatch(createGoal({ payload: payload }))
    }

    if (mode === 'edit' && goal) {
      dispatch(
        editGoal({
          goalId: goal.goalId,
          ...payload,
        }),
      )
    }

    onClose()
  }

  const title = mode === 'edit' ? 'editGoal' : 'createGoal'
  const buttonTitle = mode === 'edit' ? 'edit' : 'create'
  return (
    <ModalLayout>
      <IconButton onClick={onClose} sx={{ position: 'absolute', top: 12, right: 12 }}>
        <CloseOutlined sx={{ color: 'link.main' }} />
      </IconButton>

      <Stack
        spacing={3}
        sx={{ width: '100%', justifyContent: 'center', textAlign: 'center', height: '100%' }}
      >
        <Typography variant="h2">{translate(title)}</Typography>

        <form onSubmit={handleSubmit}>
          <Stack spacing={2} width={'100%'} px={4}>
            <TextField
              label={translate('name')}
              value={values.name}
              onChange={handleChange('name')}
              required
            />

            <TextField
              label={translate('value')}
              type="number"
              value={values.targetValue}
              onChange={handleChange('targetValue')}
              slotProps={{ htmlInput: { min: 0 } }}
              required
            />

            <LocalizationProvider dateAdapter={AdapterDayjs}>
              <DatePicker
                label={translate('date')}
                value={values.finishDate ? dayjs(values.finishDate) : null}
                onChange={(newValue: Dayjs | null) => {
                  setValues((prev) => ({
                    ...prev,
                    finishDate: newValue ? newValue.format('YYYY-MM-DD') : '',
                  }))
                }}
                disablePast
              />
            </LocalizationProvider>

            <Stack direction="row" spacing={2} justifyContent="flex-end">
              <Button type="submit" variant="contained" disabled={!canSubmit()}>
                {translate(buttonTitle)}
              </Button>
            </Stack>
          </Stack>
        </form>
      </Stack>
    </ModalLayout>
  )
}
