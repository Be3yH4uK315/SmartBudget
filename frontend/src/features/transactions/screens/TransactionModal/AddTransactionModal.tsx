import { useEffect } from 'react'
import { STATUSES, TYPES } from '@features/transactions/constants'
import { useAddTransactionForm } from '@features/transactions/hooks'
import {
  addTransaction,
  clearAvailableGoals,
  getGoalsNames,
  selectAvailableGoals,
} from '@features/transactions/store'
import { CloseOutlined } from '@mui/icons-material'
import {
  Button,
  Chip,
  IconButton,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { DatePicker, LocalizationProvider } from '@mui/x-date-pickers'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { CategoryOption, StyledBox } from '@shared/components'
import { CATEGORIES_ICONS_MAP, CATEGORY_IDS } from '@shared/constants'
import { useTranslate } from '@shared/hooks'
import ModalLayout from '@shared/screens/ModalProvider'
import { useAppDispatch, useAppSelector } from '@shared/store'
import dayjs from 'dayjs'

type Props = {
  onClose: () => void
}

export const AddTransactionModal = ({ onClose }: Props) => {
  const dispatch = useAppDispatch()
  const translate = useTranslate('Transactions.Modal.AddTransaction')

  const availableGoals = useAppSelector(selectAvailableGoals)

  const {
    values,
    handleChange,
    handleDateChange,
    setType,
    setStatus,
    handleCategoryChange,
    handleGoalChange,
    canSubmit,
    setPayload,
  } = useAddTransactionForm()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!canSubmit()) return

    const payload = setPayload()

    await dispatch(addTransaction(payload)).unwrap().finally(onClose)
  }

  useEffect(() => {
    dispatch(getGoalsNames())

    return () => {
      dispatch(clearAvailableGoals())
    }
  }, [dispatch])

  return (
    <ModalLayout>
      <IconButton
        onClick={onClose}
        sx={{
          position: 'absolute',
          top: 12,
          right: 12,
        }}
      >
        <CloseOutlined sx={{ color: 'link.main' }} />
      </IconButton>

      <Stack spacing={4} sx={{ p: 3, alignItems: 'center' }}>
        <Typography variant="h4">{translate('title')}</Typography>

        <form onSubmit={handleSubmit}>
          <Stack spacing={2} width={'100%'} px={4}>
            <Stack direction={'row'} spacing={2}>
              <TextField
                label={translate('amount')}
                type="number"
                value={values.amount}
                onChange={handleChange('amount')}
                slotProps={{ htmlInput: { min: 1 } }}
                required
                sx={{ width: '50%' }}
              />

              <TextField
                label={translate('merchant')}
                value={values.merchant}
                onChange={handleChange('merchant')}
                required
                sx={{ width: '50%' }}
              />
            </Stack>

            <Stack direction={'row'} spacing={2}>
              <Select
                value={values.accountId ?? ''}
                displayEmpty
                onChange={handleGoalChange}
                renderValue={(accountId) => {
                  if (!accountId) return translate('accountId')

                  const goal = availableGoals.find((goal) => goal.goalId === accountId)

                  return (
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography>{goal?.name}</Typography>
                    </Stack>
                  )
                }}
                sx={{ width: '50%' }}
              >
                {availableGoals.map((goal) => {
                  return (
                    <MenuItem key={goal.goalId} value={goal.goalId}>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Typography>{translate('goal', { name: goal.name })}</Typography>
                      </Stack>
                    </MenuItem>
                  )
                })}
              </Select>

              <TextField
                label={translate('mcc')}
                value={values.mcc}
                onChange={handleChange('mcc')}
                sx={{ width: '50%' }}
              />
            </Stack>

            <TextField
              label={translate('description')}
              value={values.description}
              onChange={handleChange('description')}
            />

            <Select
              value={values.categoryId ?? ''}
              displayEmpty
              onChange={handleCategoryChange}
              renderValue={(value) => {
                if (!value) return translate('selectPlaceholder')

                const Icon = CATEGORIES_ICONS_MAP.get(value)!

                return <CategoryOption value={value} Icon={Icon} />
              }}
            >
              {CATEGORY_IDS.map((categoryId) => {
                const Icon = CATEGORIES_ICONS_MAP.get(categoryId)
                return (
                  <MenuItem key={categoryId} value={categoryId}>
                    <CategoryOption value={categoryId} Icon={Icon} />
                  </MenuItem>
                )
              })}
            </Select>

            <LocalizationProvider dateAdapter={AdapterDayjs}>
              <DatePicker
                label={
                  <Stack direction={'row'}>
                    {translate('date')}

                    <Typography color="red">*</Typography>
                  </Stack>
                }
                value={values.date ? dayjs(values.date) : null}
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

            <Stack spacing={1}>
              <Typography variant="h6" textAlign={'left'}>
                <Stack direction={'row'}>
                  {translate('type')}

                  <Typography color="red">*</Typography>
                </Stack>
              </Typography>

              <StyledBox>
                {TYPES.map((type) => (
                  <Chip
                    key={type}
                    label={translate(`Types.${type}`)}
                    variant={values.transactionType === type ? 'filled' : 'outlined'}
                    color={values.transactionType === type ? 'primary' : 'default'}
                    onClick={() => setType(type)}
                  />
                ))}
              </StyledBox>
            </Stack>

            <Stack spacing={1}>
              <Typography variant="h6" textAlign={'left'}>
                <Stack direction={'row'}>
                  {translate('status')}

                  <Typography color="red">*</Typography>
                </Stack>
              </Typography>

              <StyledBox>
                {STATUSES.map((status) => (
                  <Chip
                    key={status}
                    component={'span'}
                    label={translate(`Statuses.${status}`)}
                    variant={values.status === status ? 'filled' : 'outlined'}
                    color={values.status === status ? 'primary' : 'default'}
                    onClick={() => setStatus(status)}
                  />
                ))}
              </StyledBox>
            </Stack>

            <Stack direction="row" justifyContent="flex-end">
              <Button
                sx={{ width: '100%' }}
                type={'submit'}
                variant="yellow"
                disabled={!canSubmit()}
              >
                {translate('confirm')}
              </Button>
            </Stack>

            <Typography variant="caption">{translate('infoBlock')}</Typography>
          </Stack>
        </form>
      </Stack>
    </ModalLayout>
  )
}
