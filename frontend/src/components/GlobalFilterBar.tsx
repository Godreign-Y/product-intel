import React from 'react';
import { useFilters } from './FilterContext';

export const GlobalFilterBar: React.FC = () => {
  const { 
    selectedCategory, setSelectedCategory, 
    selectedProduct, setSelectedProduct, 
    startDate, setStartDate, 
    endDate, setEndDate 
  } = useFilters();

  const products = Array.from({ length: 100 }, (_, i) => `P${String(i + 1).padStart(3, '0')}`);

  return (
    <div className="filter-bar animate-fade-in">
      <div className="filter-group">
        <label>Category</label>
        <select 
          className="filter-select" 
          value={selectedCategory} 
          onChange={(e) => {
            setSelectedCategory(e.target.value);
            setSelectedProduct(''); // clear product when category changes
          }}
        >
          <option value="">All Categories</option>
          <option value="Skincare">Skincare</option>
          <option value="Haircare">Haircare</option>
          <option value="Makeup">Makeup</option>
        </select>
      </div>

      <div className="filter-group">
        <label>Product Filter</label>
        <select 
          className="filter-select" 
          value={selectedProduct} 
          onChange={(e) => setSelectedProduct(e.target.value)}
        >
          <option value="">All Products</option>
          {products.map(p => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label>Start Date</label>
        <input 
          type="date" 
          className="filter-input"
          value={startDate}
          min="2025-01-01"
          max="2025-12-31"
          onChange={(e) => setStartDate(e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label>End Date</label>
        <input 
          type="date" 
          className="filter-input"
          value={endDate}
          min="2025-01-01"
          max="2025-12-31"
          onChange={(e) => setEndDate(e.target.value)}
        />
      </div>
    </div>
  );
};
