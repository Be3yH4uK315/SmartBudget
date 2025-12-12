import { TypographyVariantsOptions } from '@mui/material/styles'

const brandTinkoffFont =
  '"Tinkoff Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'

const brandFont =
  '"Neue Haas Unica W1G", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'

export const typography: TypographyVariantsOptions = {
  fontFamily: brandTinkoffFont,
  fontWeightRegular: '400',

  h1: {
    fontFamily: brandTinkoffFont,
    fontWeight: '600',
    fontSize: '3.125rem',
  },

  h2: {
    fontFamily: brandTinkoffFont,
    fontWeight: '600',
    fontSize: '2.75rem',
  },

  h3: {
    fontFamily: brandTinkoffFont,
    fontWeight: '500',
    fontSize: '2rem',
  },

  h4: {
    fontFamily: brandTinkoffFont,
    fontWeight: '500',
    fontSize: '1.75rem',
  },

  h5: {
    fontFamily: brandTinkoffFont,
    fontWeight: '500',
    fontSize: '1.5rem',
  },

  caption: {
    fontFamily: brandFont,
    fontWeight: '400',
    fontSize: '0.875rem',
  },

  body1: {
    fontFamily: brandFont,
    fontWeight: '400',
    fontSize: '1rem',
  },
}
