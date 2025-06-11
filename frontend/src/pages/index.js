import React, { useState } from 'react';
import axios from 'axios';
import { useForm } from 'react-hook-form';
import { ResultsTable } from '../components/ResultsTable';
import { StatsSummary } from '../components/StatsSummary';
import { FaQuestionCircle } from 'react-icons/fa'; // Adicione este import

export default function Home() {
  const defaultValues = {
    years: 2,
    num_contracts: 1000,
    early_profit_pct: 60,
    friday_type: 'primeira'
  };

  const { register, handleSubmit, formState: { errors } } = useForm({ defaultValues });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showHelp, setShowHelp] = useState(false); // Estado para o modal de ajuda

  const onSubmit = async (data) => {
    setLoading(true);
    setError('');
    setResults(null);

    let modifiedDaysBefore = data.days_before;
    if (data.friday_type === 'primeira') {
      modifiedDaysBefore = data.days_before - 10;
    }

    const modifiedData = {
      ...data,
      premium_pct: data.premium_pct / 2,
      days_before: modifiedDaysBefore,
    };

    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL;

    try {
      const response = await axios.post(`${backendUrl}/backtest`, modifiedData);
      if (response.data.success) {
        setResults(response.data);
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError('Erro ao conectar com o servidor: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      {/* Botão de Ajuda no canto superior direito */}
      <div className="flex justify-end mb-2">
        <button
          className="flex items-center gap-2 text-blue-600 hover:text-blue-800 font-semibold"
          onClick={() => setShowHelp(true)}
        >
          <FaQuestionCircle className="text-xl" />
          <span>Ajuda</span>
        </button>
      </div>

      {/* Modal de Ajuda */}
      {showHelp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
          <div
            className="bg-white rounded-lg shadow-lg p-2 relative overflow-auto"
            style={{
              maxWidth: '100vw',
              maxHeight: '100vh',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
            }}
          >
            <button
              className="absolute top-2 right-2 text-gray-500 hover:text-gray-700 text-2xl z-10"
              onClick={() => setShowHelp(false)}
              aria-label="Fechar"
            >
              &times;
            </button>
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2 pl-2 pt-2 w-full">
              <FaQuestionCircle className="text-blue-600" />
              Ajuda
            </h2>
            <img
              src="/Ajuda.PNG"
              alt="Ajuda"
              className="block"
              style={{
                width: 'auto',
                height: 'auto',
                maxWidth: 'none',
                maxHeight: 'none',
              }}
            />
          </div>
        </div>
      )}

      <header className="text-center mb-8">
        <h1 className="text-3xl font-bold">🎯 Sratium Backtester</h1>
        <p className="text-gray-600">Sistema de Backteste para Estratégia Strangle  </p>
      </header>

      <main>
        {/* FORMULÁRIO */}
        <div className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
          <h2 className="text-xl font-semibold mb-4">📊 Parâmetros do Backtest</h2>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Ticker:</label>
                <input
                  type="text"
                  {...register("ticker", { required: "Ticker é obrigatório" })}
                  placeholder="Ex: PETR4, VALE3"
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                />
                {errors.ticker && <p className="text-red-500 text-xs italic">{errors.ticker.message}</p>}
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Período (anos):</label>
                <select
                  {...register("years")}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                >
                  <option value={1}>1 ano</option>
                  <option value={2}>2 anos</option>
                  <option value={3}>3 anos</option>
                  <option value={4}>4 anos</option>
                  <option value={5}>5 anos</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Dias antes do vencimento:</label>
                <input
                  type="number"
                  {...register("days_before", { valueAsNumber: true })}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Range (%):</label>
                <input
                  type="number"
                  {...register("range_pct", { valueAsNumber: true })}
                  step="0.01"
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Prêmio (%):</label>
                <input
                  type="number"
                  {...register("premium_pct", { valueAsNumber: true })}
                  step="0.01"
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Contratos:</label>
                <input
                  type="number"
                  {...register("num_contracts", { valueAsNumber: true })}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Saída antecipada (%):</label>
                <input
                  type="number"
                  {...register("early_profit_pct", { valueAsNumber: true })}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                />
              </div>
              <div>
                <label className="block text-gray-700 text-sm font-bold mb-2">Sexta-feira:</label>
                <select
                  {...register("friday_type")}
                  className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                >
                  <option value="primeira">Primeira</option>
                  <option value="terceira">Terceira</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
            >
              {loading ? '⏳ Processando...' : '🚀 Executar Backtest'}
            </button>
          </form>
        </div>

        {/* ERRO */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
            <strong className="font-bold">❌ Erro</strong>
            <span className="block sm:inline">{error}</span>
          </div>
        )}

        {/* RESULTADOS */}
        {results && results.success && (
          <div>
            <StatsSummary stats={results.stats} />
            <ResultsTable trades={results.trades} />
          </div>
        )}
      </main>
    </div>
  );
}