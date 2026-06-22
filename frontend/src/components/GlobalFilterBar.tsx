import React from 'react';
import { SlidersHorizontal } from 'lucide-react';
import { useFilters } from './FilterContext';

export const GlobalFilterBar: React.FC = () => {
  const {
    selectedCategory,
    setSelectedCategory,
    selectedProduct,
    setSelectedProduct,
    startDate,
    setStartDate,
    endDate,
    setEndDate,
  } = useFilters();

  const products = Array.from({ length: 100 }, (_, i) => `P${String(i + 1).padStart(3, '0')}`);

  return (
    <div className="cozy-filter-bar animate-fade-in">
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginRight: 8, color: 'var(--cozy-rose)' }}>
        <SlidersHorizontal size={16} />
        <span style={{ fontSize: 12, fontWeight: 600, letterSpacing: '0.06em' }}>Refine your view</span>
      </div>

      <div className="filter-group">
        <label>Category</label>
        <select
          className="filter-select"
          value={selectedCategory}
          onChange={(e) => {
            setSelectedCategory(e.target.value);
            setSelectedProduct('');
          }}
        >
          <option value="">All categories</option>
          <option value="Skincare">Skincare</option>
          <option value="Haircare">Haircare</option>
          <option value="Makeup">Makeup</option>
        </select>
      </div>

      <div className="filter-group">
        <label>Product</label>
        <select
          className="filter-select"
          value={selectedProduct}
          onChange={(e) => setSelectedProduct(e.target.value)}
        >
          <option value="">All products</option>
          {products.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label>From</label>
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
        <label>To</label>
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
