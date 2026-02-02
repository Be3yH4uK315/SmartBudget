import { useState } from 'react'
import { Button, Popover, Stack, TextField, Typography } from '@mui/material'
import { DatePicker, LocalizationProvider } from '@mui/x-date-pickers'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import { useTranslate } from '@shared/hooks'
import dayjs from 'dayjs'

type NumberRangeProps = {
  labelKey: string
  type: 'number'
  from: number | undefined
  to: number | undefined
  onChangeFrom: (value?: number) => void
  onChangeTo: (value?: number) => void
  onClose: () => void
}

type DateRangeProps = {
  labelKey: string
  type: 'date'
  from: string
  to: string
  onChangeFrom: (value: string) => void
  onChangeTo: (value: string) => void
  onClose: () => void
}

type Props = NumberRangeProps | DateRangeProps

type InputProps = {
  label: string
  value: string | number | undefined
  type: 'number' | 'date'
  from: string | number | undefined
  to: string | number | undefined
  onChange: (value: any) => void
}
export function TransactionsRangePopover({
  labelKey,
  type,
  from,
  to,
  onChangeFrom,
  onChangeTo,
  onClose,
}: Props) {
  const translate = useTranslate('Transactions.Filters.Popover')

  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null)

  const open = Boolean(anchorEl)

  const handleOpen = (e: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(e.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
    onClose()
  }

  return (
    <>
      <Button variant="yellow" onClick={handleOpen} sx={{ height: 'min-content' }}>
        {translate(`${labelKey}.emptyLabel`)}
      </Button>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        slotProps={{ paper: { sx: { borderRadius: '12px' } } }}
      >
        <LocalizationProvider dateAdapter={AdapterDayjs}>
          <Stack spacing={1} sx={{ p: 2, minWidth: 240 }}>
            <Typography>{translate(`${labelKey}.emptyLabel`)}</Typography>

            {renderInput({
              label: translate(`${labelKey}.from`),
              value: from,
              type,
              from,
              to,
              onChange: onChangeFrom,
            })}

            {renderInput({
              label: translate(`${labelKey}.to`),
              value: to,
              type,
              from,
              to,
              onChange: onChangeTo,
            })}
          </Stack>
        </LocalizationProvider>
      </Popover>
    </>
  )
}

const renderInput = ({ label, value, type, from, to, onChange }: InputProps) => {
  if (type === 'number') {
    return (
      <TextField
        label={label}
        type="number"
        value={value ?? ''}
        size="small"
        slotProps={{ htmlInput: { min: 0 } }}
        onChange={(e) => {
          const v = e.target.value
          onChange(v === '' ? undefined : Math.max(0, Number(v)))
        }}
      />
    )
  }

  return (
    <DatePicker
      label={label}
      value={value ? dayjs(value) : null}
      minDate={from ? dayjs(from) : undefined}
      maxDate={to ? dayjs(to) : undefined}
      onChange={(v) => onChange(v ? v.format('YYYY-MM-DD') : '')}
      format="DD.MM.YYYY"
      slots={{ textField: TextField }}
      enableAccessibleFieldDOMStructure={false}
      slotProps={{
        textField: {
          size: 'small',
          InputProps: {
            sx: {
              '& .MuiSvgIcon-root': {
                color: 'text.primary',
              },
            },
          },
        },
      }}
    />
  )
}
