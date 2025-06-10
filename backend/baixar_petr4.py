from yfinance import download
import pandas as pd

def baixar_dados_ajustados(ticker, periodo, arquivo_saida):
    # Baixa dados ajustados (auto_adjust=True)
    dados = download(ticker, period=periodo, auto_adjust=True)

    # Salva em CSV
    dados.to_csv(arquivo_saida, sep=';', decimal=',', encoding='utf-8')
    print(f'Dados salvos em {arquivo_saida}')
    print(dados.head())

if __name__ == "__main__":
    ticker = "BOVA11.SA"
    periodo = "2y"  # 2 anos
    arquivo_saida = "bova11_ajustado.csv"

    baixar_dados_ajustados(ticker, periodo, arquivo_saida)