import { useTransactionsSearch } from '@features/transactions/hooks'
import { TransactionLine } from '@features/transactions/screens/TransactionsScreen/TransactionsList'
import { Search } from '@mui/icons-material'
import { Autocomplete, Box, CircularProgress, InputAdornment, TextField } from '@mui/material'
import { StyledPaper } from '@shared/components'
import { useTheme, useTranslate } from '@shared/hooks'

export const SearchBar = () => {
  const translate = useTranslate('Transactions.SearchBar')
  const theme = useTheme()

  const { options, isLoading, inputValue, setInputValue } = useTransactionsSearch()

  const bgColor = theme.colorMode === 'light' ? 'surface.dark' : 'surface.light'

  return (
    <Autocomplete
      options={options}
      value={null}
      filterOptions={(x) => x}
      noOptionsText={isLoading ? '' : translate('emptyResult')}
      open={!!inputValue.trim()}
      onInputChange={(_, value) => setInputValue(value)}
      popupIcon={false}
      slotProps={{
        paper: {
          component: (props) => (
            <StyledPaper
              elevation={0}
              {...props}
              paperSx={{
                mt: 1,
                '& .MuiAutocomplete-noOptions': {
                  color: 'text.primary',
                  textAlign: 'center',
                  py: 2,
                },
              }}
            >
              {isLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                  <CircularProgress size={20} />
                </Box>
              ) : (
                <>{props.children}</>
              )}
            </StyledPaper>
          ),
        },
      }}
      renderOption={(props, option) => (
        <TransactionLine {...props} key={option.transactionId} transaction={option} />
      )}
      renderInput={(params) => (
        <TextField
          {...params}
          placeholder={translate('placeholder')}
          hiddenLabel
          slotProps={{
            input: {
              ...params.InputProps,
              startAdornment: (
                <InputAdornment position="start" sx={{ pl: 1 }}>
                  <Search sx={{ color: 'gray.main' }} />
                </InputAdornment>
              ),
            },
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              backgroundColor: bgColor,
              borderRadius: '12px',
              pr: 1.5,

              ':hover': {
                backgroundColor: bgColor,
              },

              '& fieldset': {
                borderColor: bgColor,
              },

              '&:hover fieldset': {
                borderColor: bgColor,
              },

              '&.Mui-focused fieldset': {
                borderColor: bgColor,
              },
            },
          }}
        />
      )}
    />
  )
}
