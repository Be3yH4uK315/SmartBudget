import { useState } from 'react'
import { Button, Popover, Stack, TextField, Typography } from '@mui/material'
import { DatePicker } from '@mui/x-date-pickers'
import { NumberField } from '@shared/components'
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
  value?: string | number
  type: 'number' | 'date'
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
      <Button
        variant="white"
        onClick={handleOpen}
        sx={{
          height: 'min-content',
          bgcolor: 'surface.light',
          border: '1px solid',
          borderColor: 'primary.main',
          px: 2,
        }}
      >
        {translate(`${labelKey}.emptyLabel`)}
      </Button>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
        slotProps={{ paper: { sx: { borderRadius: '12px' } } }}
      >
        <Stack spacing={1} sx={{ p: 2, minWidth: 240 }}>
          <Typography>{translate(`${labelKey}.emptyLabel`)}</Typography>

          {renderInput({
            label: translate(`${labelKey}.from`),
            value: from,
            type,
            onChange: onChangeFrom,
          })}

          {renderInput({
            label: translate(`${labelKey}.to`),
            value: to,
            type,
            onChange: onChangeTo,
          })}
        </Stack>
      </Popover>
    </>
  )
}

const renderInput = ({ label, value, type, onChange }: InputProps) => {
  if (type === 'number') {
    return <NumberField label={label} value={value} onChange={onChange} />
  }

  return (
    <DatePicker
      label={label}
      value={value ? dayjs(value) : null}
      onChange={(v) => onChange(v ? v.format('YYYY-MM-DD') : '')}
      format="DD.MM.YYYY"
      slots={{ textField: TextField }}
      enableAccessibleFieldDOMStructure={false}
      disableFuture
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
