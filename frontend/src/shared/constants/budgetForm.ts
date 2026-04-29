import { SxProps } from '@mui/material'

export const TEXT_FIELD_SX = (color: string): SxProps => ({
  '& .MuiOutlinedInput-root': {
    backgroundColor: color,

    '& fieldset': {
      borderColor: color,
    },

    '&:hover': {
      backgroundColor: color,

      '& fieldset': {
        borderColor: color,
      },

      '& .MuiInputAdornment-root': {
        color: 'text.primary',
      },
    },

    '&.Mui-focused': {
      backgroundColor: color,

      '& fieldset': {
        borderColor: color,
      },

      '& .MuiInputAdornment-root': {
        color: 'text.primary',
      },
    },
  },

  '& input::-webkit-outer-spin-button, & input::-webkit-inner-spin-button': {
    WebkitAppearance: 'none',
    margin: 0,
  },
})
