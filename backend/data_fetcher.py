import yfinance as yf

def baixar_dados_ajustados(ticker: str, periodo_anos: int = 2):
    """
    Baixa dados ajustados do yfinance para o ticker e período especificados.
    Retorna um DataFrame pandas com os dados.
    """
    dados = yf.download(ticker, period=f"{periodo_anos}y", auto_adjust=True)
    if dados.empty:
        raise ValueError(f"Nenhum dado encontrado para o ticker {ticker}")
    return dados