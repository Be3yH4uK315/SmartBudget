import { forwardRef } from 'react'
import { Box, CircularProgress, List, ListItem } from '@mui/material'
import { GroupedVirtuosoProps } from 'react-virtuoso'

type FooterProps = {
  isLast: boolean
  isLoading: boolean
}

export const MUIComponents: GroupedVirtuosoProps<unknown, unknown>['components'] = {
  List: forwardRef(({ style, children, ...props }, ref) => (
    <List
      ref={ref}
      {...props}
      component="div"
      style={{ ...style }}
      sx={{ padding: 0, margin: 0, maxWidth: '800px' }}
    >
      {children}
    </List>
  )),

  Item: ({ children, ...props }) => (
    <ListItem component={'div'} {...props} sx={{ px: 0, py: 1 }}>
      {children}
    </ListItem>
  ),

  Group: ({ children }) => (
    <Box component={'div'} sx={{ bgcolor: 'surface.main', py: 2 }}>
      {children}
    </Box>
  ),
}

export const ListFooter = ({ isLast, isLoading }: FooterProps) => {
  return (
    <Box sx={{ display: 'flex', maxWidth: '800px', justifyContent: 'center', py: 2 }}>
      {!isLast && isLoading && <CircularProgress size={24} />}
    </Box>
  )
}
