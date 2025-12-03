import { ThemeOptions } from '@mui/material'
import NeueRegular from '@shared/assets/fonts/Neue Haas Unica W1G Light.ttf'
import TinkoffSansBold from '@shared/assets/fonts/TinkoffSans-Bold.ttf'
import TinkoffSansMedium from '@shared/assets/fonts/TinkoffSans-Medium.ttf'

export const components: ThemeOptions['components'] = {
  MuiCssBaseline: {
    styleOverrides: (theme) => ({
      '[data-color-scheme="dark"]': {
        colorScheme: 'dark',
      },

      '[data-color-scheme="light"]': {
        colorScheme: 'light',
      },

      '#root': {
        backgroundColor: theme.palette.surface.main,
      },

      '@font-face': [
        {
          fontFamily: 'Neue Haas Unica W1G',
          fontWeight: '400',
          src: `url(${NeueRegular}) format('truetype')`,
        },
        {
          fontFamily: 'Tinkoff Sans',
          fontWeight: '500',
          src: `url(${TinkoffSansMedium}) format('truetype')`,
        },
        {
          fontFamily: 'Tinkoff Sans',
          fontWeight: '600',
          src: `url(${TinkoffSansBold}) format('truetype')`,
        },
      ],
    }),
  },

  MuiButton: {
    defaultProps: {
      disableElevation: true,
      variant: 'gray',
    },

    styleOverrides: {
      root: ({ theme }) => ({
        textTransform: 'none',
        minWidth: 'auto',
        padding: '8px 16px',
        height: '56px',

        ...theme.typography.body1,

        borderWidth: 0,
        borderStyle: 'solid',

        borderRadius: '12px',
      }),
    },

    variants: [
      {
        props: { variant: 'gray' },
        style: ({ theme }) => ({
          backgroundColor: theme.palette.grayButton.main,
          color: theme.palette.secondary.main,

          '&:hover': {
            backgroundColor: theme.palette.grayButton.dark,
            color: theme.palette.secondary.light,
          },
          '&:active': {
            backgroundColor: theme.palette.grayButton.dark,
            color: theme.palette.secondary.dark,
          },
          '&.Mui-disabled': {
            backgroundColor: theme.palette.gray.light,
            color: theme.palette.gray.main,
          },
        }),
      },

      {
        props: { variant: 'yellow' },
        style: ({ theme }) => ({
          backgroundColor: theme.palette.primary.main,
          color: '#333333',

          '&:hover': {
            backgroundColor: theme.palette.primary.light,
          },
          '&:active': {
            backgroundColor: theme.palette.primary.dark,
          },
          '&.Mui-disabled': {
            backgroundColor: theme.palette.gray.light,
            color: theme.palette.gray.main,
          },
        }),
      },

      {
        props: { variant: 'blue' },
        style: ({ theme }) => ({
          backgroundColor: theme.palette.secondary.main,
          color: '#FFFFFF',

          '&:hover': {
            backgroundColor: theme.palette.secondary.light,
          },
          '&:active': {
            backgroundColor: theme.palette.secondary.dark,
          },
          '&.Mui-disabled': {
            backgroundColor: theme.palette.gray.light,
            color: theme.palette.gray.main,
          },
        }),
      },

      {
        props: { variant: 'link' },
        style: ({ theme }) => ({
          backgroundColor: 'transparent',
          color: theme.palette.link.main,
          padding: 0,
          margin: 0,
          typography: 'caption',
          width: 'max-content',

          '&:hover': {
            backgroundColor: 'transparent',
            color: theme.palette.link.dark,
          },
          '&:active': {
            backgroundColor: 'transparent',
            color: theme.palette.link.light,
          },
        }),
      },

      {
        props: { variant: 'white' },
        style: ({ theme }) => ({
          backgroundColor: theme.palette.grayButton.light,
          color: theme.palette.text.primary,
          padding: '6px',
          margin: 0,
          borderWidth: 2,
          borderColor: 'transparent',
          typography: 'caption',
          width: 'min-content',
          height: 'min-content',

          '&:hover': {
            backgroundColor: theme.palette.grayButton.main,
          },
          '&:active': {
            backgroundColor: 'transparent',
          },
        }),
      },
    ],
  },

  MuiTypography: {
    defaultProps: {
      variant: 'body1',
    },
    styleOverrides: {
      root({ theme }) {
        return { color: theme.palette.text.primary }
      },
    },
  },

  MuiTooltip: {
    styleOverrides: {
      tooltip: ({ theme: { palette, typography } }) => ({
        color: palette.text.primary,
        backgroundColor: palette.gray.dark,
        ...typography.caption,
      }),
    },
  },

  MuiSkeleton: {
    defaultProps: {
      variant: 'rounded',
    },

    styleOverrides: {
      root: ({ theme: { palette } }) => ({
        animation: `pulse 2s ease-in-out infinite`,
        backgroundColor: palette.gray.main,

        '@keyframes pulse': {
          '0%': {
            opacity: 1,
          },
          '50%': {
            opacity: 0.3,
          },
          '100%': {
            opacity: 1,
          },
        },
      }),

      rounded: {
        borderRadius: '24px',
      },
    },
  },

  MuiLink: {
    styleOverrides: {
      root: ({ theme }) => ({
        color: theme.palette.link.main,
        overflowWrap: 'break-word',
      }),
    },
  },

  MuiTab: {
    styleOverrides: {
      root: ({ theme }) => ({
        textTransform: 'none',
        minHeight: 48,
        ...theme.typography.caption,
        color: theme.palette.text.primary,

        paddingInline: theme.spacing(0),
        [theme.breakpoints.up('sm')]: {
          paddingInline: theme.spacing(2),
        },

        '&.Mui-selected': {
          color: theme.palette.text.primary,
        },
      }),
    },
  },

  MuiTextField: {
    styleOverrides: {
      root: ({ theme }) => ({
        '& .MuiOutlinedInput-root': {
          height: '56px',
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: theme.palette.primary.main,
            borderWidth: '2px',
            borderRadius: '12px',
          },
          '&:hover:not(.Mui-focused)': {
            '& .MuiOutlinedInput-notchedOutline': {
              borderColor: theme.palette.primary.light,
            },
          },
        },
        '& .MuiInputLabel-outlined': {
          color: theme.palette.text.primary,
          '&.Mui-focused': {
            color: theme.palette.text.primary,
          },
        },
      }),
    },
  },

  MuiPaper: {
    styleOverrides: {
      root: ({ theme }) => ({
        backgroundColor: theme.palette.surface.light,
      }),
    },
  },
}
