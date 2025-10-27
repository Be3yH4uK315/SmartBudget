import { TypographyVariantsOptions } from '@mui/material/styles'

const brandFont =
  '"Tinkoff Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'

export const typography: TypographyVariantsOptions = {
  fontFamily: brandFont,
  fontWeightRegular: '400',

  h1: {
    fontFamily: brandFont,
    fontWeight: '600',
    fontSize: '3.125rem',
  },

  h2: {
    fontFamily: brandFont,
    fontWeight: '600',
    fontSize: '2.75rem',
  },

  h3: {
    fontFamily: brandFont,
    fontWeight: '500',
    fontSize: '2rem',
  },

  h4: {
    fontFamily: brandFont,
    fontWeight: '500',
    fontSize: '1.75rem',
  },

  h5: {
    fontFamily: brandFont,
    fontWeight: '400',
    fontSize: '1.5rem',
  },

  caption: {
    fontFamily: brandFont,
    fontWeight: '400',
    fontSize: '1.25rem',
  },

  body1: {
    fontFamily: brandFont,
    fontWeight: '400',
    fontSize: '1.25rem',
  },
}
