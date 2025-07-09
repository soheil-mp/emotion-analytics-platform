import React from 'react';
import { Box, InputBase, InputAdornment, IconButton } from '@mui/material';
import { styled } from '@mui/material/styles';
import SearchIcon from '@mui/icons-material/Search';
import ClearIcon from '@mui/icons-material/Clear';
import { motion } from 'framer-motion';

const SearchContainer = styled(motion.div)(({ theme }) => ({
  position: 'relative',
  borderRadius: 14,
  backgroundColor: 'rgba(255, 255, 255, 0.7)',
  width: '100%',
  marginBottom: theme.spacing(2),
  backdropFilter: 'blur(8px)',
  boxShadow: '0 2px 10px rgba(0, 0, 0, 0.03)',
  border: '1px solid rgba(229, 231, 235, 0.8)',
  transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
  '&:hover': {
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)',
  },
  '&.Mui-focused': {
    backgroundColor: '#fff',
    boxShadow: '0 6px 16px rgba(99, 102, 241, 0.1)',
    border: '1px solid rgba(99, 102, 241, 0.3)',
  }
}));

const StyledInputBase = styled(InputBase)(({ theme }) => ({
  color: theme.palette.text.primary,
  width: '100%',
  height: '44px',
  fontWeight: 500,
  '& .MuiInputBase-input': {
    padding: theme.spacing(1, 1, 1, 1.5),
    paddingRight: `calc(1em + ${theme.spacing(4)})`,
    transition: theme.transitions.create('width'),
    width: '100%',
    [theme.breakpoints.up('md')]: {
      width: '100%',
    },
  },
}));

const ClearButton = styled(IconButton)(({ theme }) => ({
  position: 'absolute',
  right: 0,
  top: '50%',
  transform: 'translateY(-50%)',
  padding: theme.spacing(0.5),
  color: theme.palette.text.secondary,
  '&:hover': {
    color: theme.palette.text.primary,
    backgroundColor: 'rgba(0, 0, 0, 0.04)',
  }
}));

const SearchBar = ({ value, onChange, onClear, placeholder = "Search videos..." }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
    >
      <Box sx={{ position: 'relative' }}>
        <SearchContainer className={value ? 'Mui-focused' : ''}>
          <StyledInputBase
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            startAdornment={
              <InputAdornment position="start">
                <SearchIcon
                  fontSize="small"
                  sx={{
                    ml: 0.5,
                    color: 'text.secondary',
                    opacity: 0.7
                  }}
                />
              </InputAdornment>
            }
            inputProps={{ 'aria-label': 'search' }}
            className="search-input"
          />
        </SearchContainer>
        {value && (
          <ClearButton
            aria-label="clear search"
            onClick={onClear}
            size="small"
          >
            <ClearIcon fontSize="small" />
          </ClearButton>
        )}
      </Box>
    </motion.div>
  );
};

export default SearchBar;
