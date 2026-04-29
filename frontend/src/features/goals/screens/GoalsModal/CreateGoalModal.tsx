import 'dayjs/locale/ru'
import { AVAILABLE_TAGS, MAX_TAGS_LENGTH, PRIORITIES } from '@features/goals/constants/tags'
import { useGoalModalForm } from '@features/goals/hooks'
import { editGoal } from '@features/goals/store/currentGoal'
import { createGoal } from '@features/goals/store/goals'
import { Goal } from '@features/goals/types'
import { Button, Chip, Stack, TextField, Typography } from '@mui/material'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { CloseModalButton, StyledBox } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import ModalLayout from '@shared/screens/ModalProvider'
import { useAppDispatch } from '@shared/store'
import dayjs from 'dayjs'

type Props = {
  goal?: Goal
  onClose: () => void
}

export const GoalModal = ({ onClose, goal }: Props) => {
  const translate = useTranslate('Goals')
  const dispatch = useAppDispatch()

  const {
    dirty,
    mode,
    values,
    handleChange,
    handleDateChange,
    setPriority,
    toggleTag,
    canSubmit,
    setPayload,
  } = useGoalModalForm(goal)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!canSubmit() || !dirty) return

    const payload = setPayload(goal?.status)

    if (mode === 'create') dispatch(createGoal({ payload }))
    if (mode === 'edit' && goal) dispatch(editGoal({ ...payload, goalId: goal.goalId }))

    onClose()
  }

  const title = mode === 'edit' ? 'Modal.editTitle' : 'Modal.createTitle'
  const buttonTitle = mode === 'edit' ? 'Modal.editButton' : 'Modal.createButton'

  return (
    <ModalLayout>
      <CloseModalButton onClose={onClose} />

      <Stack
        spacing={3}
        sx={{ width: '100%', justifyContent: 'center', textAlign: 'center', height: '100%' }}
      >
        <Typography variant="h2">{translate(title)}</Typography>

        <form onSubmit={handleSubmit}>
          <Stack spacing={2} width={'100%'} px={4}>
            <TextField
              label={translate('Modal.name')}
              value={values.name}
              onChange={handleChange('name')}
              required
            />

            <TextField
              label={translate('Modal.value')}
              type="number"
              value={values.targetValue}
              onChange={handleChange('targetValue')}
              slotProps={{ htmlInput: { min: 1 } }}
              required
            />

            <LocalizationProvider dateAdapter={AdapterDayjs}>
              <DatePicker
                label={translate('Modal.date')}
                value={values.finishDate ? dayjs(values.finishDate) : null}
                onChange={handleDateChange}
                format="DD.MM.YYYY"
                slots={{ textField: TextField }}
                enableAccessibleFieldDOMStructure={false}
                slotProps={{
                  textField: {
                    InputProps: {
                      sx: {
                        '& .MuiSvgIcon-root': {
                          color: 'text.primary',
                        },
                      },
                    },
                  },
                }}
                disablePast
              />
            </LocalizationProvider>

            <Typography variant="h6" textAlign={'left'}>
              {translate('Modal.priorityTags')}
            </Typography>

            <StyledBox>
              {PRIORITIES.map((tag) => (
                <Chip
                  key={tag}
                  label={translate(`Tags.${tag}`)}
                  variant={values.priority === tag ? 'filled' : 'outlined'}
                  color={values.priority === tag ? 'primary' : 'default'}
                  onClick={() => setPriority(tag)}
                />
              ))}
            </StyledBox>

            <Typography variant="h6" textAlign={'left'}>
              {translate('Modal.otherTags')}
            </Typography>

            <StyledBox>
              {AVAILABLE_TAGS.map((tag) => (
                <Chip
                  key={tag}
                  component={'span'}
                  label={translate(`Tags.${tag}`)}
                  variant={values.tags.includes(tag) ? 'filled' : 'outlined'}
                  color={values.tags.includes(tag) ? 'primary' : 'default'}
                  onClick={() => toggleTag(tag)}
                  disabled={!values.tags.includes(tag) && values.tags.length >= MAX_TAGS_LENGTH}
                  sx={{ display: 'inline-flex' }}
                />
              ))}
            </StyledBox>

            <Stack direction="row" justifyContent="flex-end">
              <Button type="submit" variant="yellow">
                {translate(buttonTitle)}
              </Button>
            </Stack>
          </Stack>
        </form>
      </Stack>
    </ModalLayout>
  )
}
