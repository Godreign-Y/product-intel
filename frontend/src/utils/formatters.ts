// Format helper for currency
export const formatCurrency = (val: number) => {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);
};

// Format helper for large numbers
export const formatNumber = (val: number) => {
  return new Intl.NumberFormat('en-US').format(val);
};
