import React, { createContext, useContext, useState } from 'react';
import { FilterContextType } from '../types';

const FilterContext = createContext<FilterContextType | undefined>(undefined);

export const FilterProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedProduct, setSelectedProduct] = useState('P001');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [startDate, setStartDate] = useState('2025-01-01');
  const [endDate, setEndDate] = useState('2025-12-31');

  return (
    <FilterContext.Provider value={{
      selectedProduct, setSelectedProduct,
      selectedCategory, setSelectedCategory,
      startDate, setStartDate,
      endDate, setEndDate
    }}>
      {children}
    </FilterContext.Provider>
  );
};

export const useFilters = () => {
  const context = useContext(FilterContext);
  if (!context) throw new Error('useFilters must be used within a FilterProvider');
  return context;
};
