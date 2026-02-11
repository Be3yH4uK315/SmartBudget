import { SxProps, TextField, TextFieldProps, Typography } from '@mui/material'

type Props = {
  label: string
  type?: 'number' | 'percent'
  value?: string | number
  onChange: (value: any) => void
  textFieldProps?: TextFieldProps
  textFieldSx?: SxProps
}

export const NumberField = ({
  label,
  type = 'number',
  value,
  onChange,
  textFieldProps,
  textFieldSx,
}: Props) => {
  return (
    <TextField
      label={label}
      type="text"
      value={value ?? ''}
      slotProps={{
        htmlInput: {
          min: 0,
        },
        input: {
          endAdornment: <Typography>{type === 'number' ? '₽' : '%'}</Typography>,
          inputMode: 'numeric',
        },
        inputLabel: { shrink: value !== undefined && value !== null && value !== '' },
      }}
      onKeyDown={(e) => {
        if (e.key === '-' || e.key === 'e' || e.key === 'E' || e.key === '+') {
          e.preventDefault()
        }
      }}
      onPaste={(e) => {
        const text = e.clipboardData.getData('text')
        if (/[-eE+]/.test(text)) {
          e.preventDefault()
        }
      }}
      onChange={(e) => {
        const raw = e.target.value

        if (raw === '') {
          onChange(undefined)
          return
        }

        if (!/^\d+$/.test(raw)) {
          return
        }

        const num = parseInt(raw, 10)
        if (!Number.isFinite(num)) return

        onChange(num)
      }}
      sx={{
        '& input::-webkit-outer-spin-button, & input::-webkit-inner-spin-button': {
          WebkitAppearance: 'none',
          margin: 0,
        },
        ...textFieldSx,
      }}
      {...textFieldProps}
    />
  )
}
