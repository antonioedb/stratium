import React, { useEffect } from 'react';
import axios from 'axios';

export default function Home() {
  useEffect(() => {
    // Imprime a variável de ambiente no console
    console.log('Backend URL:', process.env.NEXT_PUBLIC_BACKEND_URL);

    // Dados para enviar no POST
    const data = {
      ticker: "PETR4.SA",
      years: 2,
      dias_antes_vencimento: 21,
      percentual_distancia: 4.95,
      percentual_premio: 1.71,
      quantidade_opcoes: 1000,
      percentual_atingida: 60.0,
      dia_vencimento: "primeira"
    };

    // Função para fazer a requisição POST
    const testBackend = async () => {
      try {
        const response = await axios.post(
          `${process.env.NEXT_PUBLIC_BACKEND_URL}/backtest`,
          data
        );
        console.log('Resposta do backend:', response.data);
      } catch (error) {
        console.error('Erro ao conectar com o backend:', error);
      }
    };

    testBackend();
  }, []);

  return (
    <div>
      <h1>Teste de conexão com backend</h1>
      <p>Abra o console do navegador para ver os logs.</p>
    </div>
  );
}