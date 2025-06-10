// src/components/StatsSummary.js
import React from 'react';

const formatCurrency = (value) =>
  new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0);

const formatPercent = (value) => {
  if (value === undefined || value === null || isNaN(value)) return '0.00%';
  return `${value.toFixed(2)}%`;
};

export const StatsSummary = ({ stats }) => {
  return (
  <div className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
    <h3 className="text-xl font-semibold mb-6">📊 Resumo Estatístico</h3>
    
    {/* Grid principal com cards */}
    <div className="grid grid-cols-2 gap-4 mb-8">
      <div className="bg-gray-50 p-4 rounded-lg border-l-4 border-blue-500">
        <h4 className="text-gray-700 text-sm font-bold mb-2">Total de Operações</h4>
        <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
      </div>
      <div className="bg-gray-50 p-4 rounded-lg border-l-4 border-green-500">
        <h4 className="text-gray-700 text-sm font-bold mb-2">Taxa de Acerto</h4>
        <p className="text-2xl font-bold text-green-600">{formatPercent(stats.win_rate)}</p>
      </div>
      <div className="bg-gray-50 p-4 rounded-lg border-l-4 border-purple-500">
        <h4 className="text-gray-700 text-sm font-bold mb-2">Resultado Total</h4>
        <p className={`text-2xl font-bold ${stats.total_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {formatCurrency(stats.total_profit)}
        </p>
      </div>
      <div className="bg-gray-50 p-4 rounded-lg border-l-4 border-orange-500">
        <h4 className="text-gray-700 text-sm font-bold mb-2">Resultado Médio</h4>
        <p className={`text-2xl font-bold ${stats.avg_profit_per_trade >= 0 ? 'text-green-600' : 'text-red-600'}`}>
          {formatCurrency(stats.avg_profit_per_trade)}
        </p>
      </div>
    </div>

    {/* Seção de Análise de Operações */}
    <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
      <h4 className="text-blue-800 text-lg font-bold mb-4 flex items-center">
        📈 Análise de Operações
      </h4>
      
    <div className="mb-4">
  <div className="flex items-center">
    <span className="font-semibold text-gray-700 mr-2">Operações que fecharam DENTRO do range:</span>
    <span className="text-xl font-bold text-blue-800 bg-blue-100 px-3 py-1 rounded">
      {stats.closed_within} <span className="text-gray-500">({Math.round((stats.closed_within / stats.total) * 100)}%)</span>
    </span>
  </div>
</div>
<div className="flex items-center">
  <span className="font-semibold text-gray-700 mr-2">Operações que ultrapassaram o range:</span>
  <span className="text-xl font-bold text-blue-800 bg-blue-100 px-3 py-1 rounded">
    {stats.exceeded} <span className="text-gray-500">({Math.round((stats.exceeded / stats.total) * 100)}%)</span>
  </span>
  
</div>
<br></br>
      {/* Grid para os detalhes */}
      <div className="grid grid-cols-3 gap-4">
        
        <div className="text-center bg-white p-4 rounded-lg shadow-sm">
          <div className="text-2xl font-bold text-red-500">{stats.exceeded_upper_only}</div>
          <div className="text-sm text-gray-600 mt-1">Apenas para cima</div>
        </div>
        <div className="text-center bg-white p-4 rounded-lg shadow-sm">
          <div className="text-2xl font-bold text-blue-500">{stats.exceeded_lower_only}</div>
          <div className="text-sm text-gray-600 mt-1">Apenas para baixo</div>
        </div>
        <div className="text-center bg-white p-4 rounded-lg shadow-sm">
          <div className="text-2xl font-bold text-purple-500">{stats.exceeded_both_count}</div>
          <div className="text-sm text-gray-600 mt-1">Para ambos os lados</div>
        </div>
      </div>
    </div>
  </div>
);
};