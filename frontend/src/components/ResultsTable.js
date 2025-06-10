// src/components/ResultsTable.js
import React from 'react';
import { FaArrowUp, FaArrowDown, FaExchangeAlt } from 'react-icons/fa';

const formatCurrency = (value) => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  }).format(value);
};

const formatPercent = (value) => {
  return `${value.toFixed(2)}%`;
};

// Função para retornar a seta colorida conforme direção
const getArrow = (trade) => {
  if (trade.exceeded_upper && trade.exceeded_lower) {
    return <FaExchangeAlt style={{ color: 'darkred' }} />; // Ambas as direções (vermelho escuro)
  } else if (trade.exceeded_upper) {
    return <FaArrowUp style={{ color: 'green' }} />; // Para cima (verde)
  } else if (trade.exceeded_lower) {
    return <FaArrowDown style={{ color: 'red' }} />; // Para baixo (vermelho)
  } else {
    return ''; // Nenhuma seta
  }
};

export const ResultsTable = ({ trades }) => {
  return (
    <div className="mt-8">
      <h3 className="text-xl font-semibold mb-4">📋 Histórico de Trades</h3>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white">
          <thead>
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Abertura</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fechamento</th>
              {/* <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Preço Inicial</th> */}
              {/* <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Preço Final</th> */}
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mudança de preços</th>
              <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Furou Range</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Resultado</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Resultado %</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dias</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Saída Antecipada</th>
              
            </tr>
          </thead>
          <tbody>
            {trades.map((trade, index) => {
              const priceChangePct = ((trade.final_price - trade.opening_price) / trade.opening_price) * 100;
              const isOutOfRange = trade.final_price > trade.upper_strike || trade.final_price < trade.lower_strike;
              const priceChangeClass = isOutOfRange ? (priceChangePct >= 0 ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold') : '';

              return (
                <tr key={index} className={index % 2 === 0 ? 'bg-gray-100' : ''}>
                  <td className="px-6 py-4 whitespace-nowrap">{new Date(trade.open_date).toLocaleDateString('pt-BR')}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{new Date(trade.close_date).toLocaleDateString('pt-BR')}</td>
                  {/* <td className="px-6 py-4 whitespace-nowrap">{formatCurrency(trade.opening_price)}</td> */}
                  {/* <td className="px-6 py-4 whitespace-nowrap">{formatCurrency(trade.final_price)}</td> */}
                  <td className={`px-6 py-4 whitespace-nowrap ${priceChangeClass}`}>
                    {formatPercent(priceChangePct)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-center">{getArrow(trade)}</td>
                  <td className={`px-6 py-4 whitespace-nowrap ${trade.trade_result >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {formatCurrency(trade.trade_result)}
                  </td>
                  <td className={`px-6 py-4 whitespace-nowrap ${trade.trade_result_pct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {formatPercent(trade.trade_result_pct)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">{trade.days_held}</td>
                  <td className="px-6 py-4 whitespace-nowrap">{trade.early_exit ? '✅' : '❌'}</td>
                  
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};