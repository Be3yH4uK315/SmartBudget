import { TextField, TextFieldProps, Typography } from '@mui/material'

type Props = {
  label: string
  value?: string | number
  onChange: (value: any) => void
  textFieldProps?: TextFieldProps
}

export const NumberField = ({ label, value, onChange, textFieldProps }: Props) => {
  return (
    <TextField
      label={label}
      type="number"
      value={value ?? ''}
      size="small"
      slotProps={{
        htmlInput: {
          min: 0,
        },
        input: { endAdornment: <Typography>₽</Typography> },
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
        const v = e.target.value
        onChange(v === '' ? undefined : Math.max(0, Number(v)))
      }}
      sx={{
        '& input::-webkit-outer-spin-button, & input::-webkit-inner-spin-button': {
          WebkitAppearance: 'none',
          margin: 0,
        },
      }}
      {...textFieldProps}
    />
  )
}
