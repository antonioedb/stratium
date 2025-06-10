# backend/main.py (continuação)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')

app = FastAPI(title="Strangle Backtester API")

# Configurar CORS

origins = [
    "http://localhost:3000",  # Permite requisições do seu frontend local
    "https://stratium.vercel.app",  # Permite requisições da sua URL do Vercel
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BacktestRequest(BaseModel):
    ticker: str
    years: int  # 1 a 5 anos
    days_before: int = 21
    range_pct: float = 4.95
    premium_pct: float = 1.71
    num_contracts: int = 1000
    early_profit_pct: int = 60
    friday_type: str = "primeira"  # "primeira" ou "terceira"

class BacktestResponse(BaseModel):
    success: bool
    message: str
    stats: Optional[dict] = None
    trades: Optional[list] = None

def nth_friday(year: int, month: int, n: int):
    """Retorna a data da n-ésima sexta-feira do mês."""
    count = 0
    for day in range(1, 32):
        try:
            d = datetime(year, month, day)
        except ValueError:
            break
        if d.weekday() == 4:  # 4 = sexta-feira
            count += 1
            if count == n:
                return d
    return None

def black_scholes(S, K, T, r, sigma, option_type="call"):
    """Calcula o preço de uma opção usando o modelo Black-Scholes."""
    if T <= 0:
        if option_type == "call":
            return max(0, S - K)
        else:
            return max(0, K - S)

    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "call":
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:  # put
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

    return price

def calculate_historical_volatility(prices, window=30):
    """Calcula a volatilidade histórica do ativo."""
    returns = np.log(prices / prices.shift(1)).dropna()
    rolling_std = returns.rolling(window=window).std()
    volatility = rolling_std * np.sqrt(252)
    return volatility

def get_yfinance_data(ticker: str, years: int):
    """Busca dados do yfinance para o período especificado."""
    try:
        # Adiciona .SA se for ação brasileira e não tiver sufixo
        if not any(suffix in ticker.upper() for suffix in ['.SA', '.TO', '.L']):
            ticker = f"{ticker}.SA"
        
        # Calcula período
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        # Busca dados
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        
        if df.empty:
            return None
            
        # Renomeia colunas para o padrão do script original
        df = df.reset_index()
        df.columns = ['Data', 'Abertura', 'Máximo', 'Mínimo', 'Fechamento', 'Volume', 'Dividends', 'Stock Splits']
        
        # Remove colunas desnecessárias
        df = df[['Data', 'Abertura', 'Máximo', 'Mínimo', 'Fechamento', 'Volume']]

        # *** ADICIONE ESTA LINHA AQUI ***
        df['Data'] = pd.to_datetime(df['Data']).dt.tz_localize(None)
        
        return df
        
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return None

def backtest_strangle_yfinance(df, days_before=21, range_pct=4.95, premium_pct=1.71,
                              num_contracts=1000, early_profit_pct=60, friday_type="primeira"):
    """Executa o backteste usando dados do yfinance."""
    
    friday_n = 1 if friday_type.lower() == "primeira" else 3
    
    # Calcula volatilidade histórica
    df["volatility"] = calculate_historical_volatility(df["Fechamento"])
    mean_volatility = df["volatility"].mean()
    if np.isnan(mean_volatility):
        mean_volatility = 0.25
    df["volatility"] = df["volatility"].fillna(mean_volatility)
    
    # Taxa de juros livre de risco
    risk_free_rate = 0.1475
    
    # Adiciona coluna de dia da semana
    df['weekday'] = df['Data'].dt.weekday
    business_days = df[df['weekday'] <= 4].copy()
    
    results = []
    trades = []
    
    start = df['Data'].min()
    end = df['Data'].max()
    
    cur_year = start.year
    cur_month = start.month
    
    while (cur_year < end.year) or (cur_year == end.year and cur_month <= end.month):
        # Encontra a sexta-feira do mês
        expiration_date = nth_friday(cur_year, cur_month, friday_n)
        
        if expiration_date is None or expiration_date < start or expiration_date > end:
            cur_month += 1
            if cur_month == 13:
                cur_month = 1
                cur_year += 1
            continue
        
        # Garante que existe nos dados
        expiration_rows = df[df['Data'] == expiration_date]
        if expiration_rows.empty:
            tmp = df[df['Data'] < expiration_date]['Data']
            if tmp.empty:
                cur_month += 1
                if cur_month == 13:
                    cur_month = 1
                    cur_year += 1
                continue
            expiration_date = tmp.iloc[-1]
        
        # Data de abertura
        before_expiration = business_days[business_days['Data'] < expiration_date]
        
        if before_expiration.empty or len(before_expiration) < days_before:
            cur_month += 1
            if cur_month == 13:
                cur_month = 1
                cur_year += 1
            continue
        
        open_date = before_expiration.iloc[-days_before]['Data']
        opening_row = df[df['Data'] == open_date].iloc[0]
        opening_price = opening_row['Fechamento']
        upper_strike = opening_price * (1 + range_pct/100)
        lower_strike = opening_price * (1 - range_pct/100)
        
        # Cálculos do Black-Scholes
        days_to_expiration = (expiration_date - open_date).days
        T_initial = days_to_expiration / 365.0
        initial_volatility = opening_row["volatility"]
        
        call_premium_bs = black_scholes(opening_price, upper_strike, T_initial, risk_free_rate, initial_volatility, "call")
        put_premium_bs = black_scholes(opening_price, lower_strike, T_initial, risk_free_rate, initial_volatility, "put")
        
        desired_premium = opening_price * premium_pct / 100
        total_premium_bs = call_premium_bs + put_premium_bs
        
        adjustment_factor = 1.0
        if total_premium_bs > 0:
            adjustment_factor = (desired_premium * 2) / total_premium_bs
        
        call_premium = call_premium_bs * adjustment_factor
        put_premium = put_premium_bs * adjustment_factor
        total_premium = (call_premium + put_premium) * num_contracts
        
        # Período de análise
        period_mask = (df['Data'] > open_date) & (df['Data'] <= expiration_date)
        period = df.loc[period_mask]
        
        if period.empty:
            cur_month += 1
            if cur_month == 13:
                cur_month = 1
                cur_year += 1
            continue
        
        early_exit_target = total_premium * early_profit_pct / 100
        early_exit = False
        early_exit_date = None
        early_exit_price = None
        
        # Análise diária para saída antecipada
        for idx, day in period.iterrows():
            current_date = day['Data']
            current_price = day['Fechamento']
            current_volatility = day["volatility"]
            
            T_remaining = (expiration_date - current_date).days / 365.0
            
            current_call_value = black_scholes(current_price, upper_strike, T_remaining, risk_free_rate, current_volatility, "call")
            current_put_value = black_scholes(current_price, lower_strike, T_remaining, risk_free_rate, current_volatility, "put")
            
            current_call_value *= adjustment_factor
            current_put_value *= adjustment_factor
            
            current_option_cost = (current_call_value + current_put_value) * num_contracts
            current_profit = total_premium - current_option_cost
            
            if current_profit >= early_exit_target:
                early_exit = True
                early_exit_date = current_date
                early_exit_price = current_price
                break
        
        # Cálculo final
        if early_exit:
            period_until_exit = df[(df['Data'] > open_date) & (df['Data'] <= early_exit_date)]
            max_price = period_until_exit['Máximo'].max()
            min_price = period_until_exit['Mínimo'].min()
            final_price = early_exit_price
            close_date = early_exit_date
            
            # Recalcula valores das opções na saída antecipada
            T_remaining = (expiration_date - early_exit_date).days / 365.0
            call_value = black_scholes(early_exit_price, upper_strike, T_remaining, risk_free_rate, 
                                     df[df['Data'] == early_exit_date].iloc[0]["volatility"], "call") * adjustment_factor
            put_value = black_scholes(early_exit_price, lower_strike, T_remaining, risk_free_rate, 
                                    df[df['Data'] == early_exit_date].iloc[0]["volatility"], "put") * adjustment_factor
            option_cost = (call_value + put_value) * num_contracts
            final_profit = total_premium - option_cost
        else:
            max_price = period['Máximo'].max()
            min_price = period['Mínimo'].min()
            final_price = period.iloc[-1]['Fechamento']
            close_date = expiration_date
            
            call_value = max(0, final_price - upper_strike)
            put_value = max(0, lower_strike - final_price)
            option_cost = (call_value + put_value) * num_contracts
            final_profit = total_premium - option_cost
        
        # Verifica se ultrapassou o range
        exceeded_upper = max_price > upper_strike 
        exceeded_lower = min_price < lower_strike
        exceeded = exceeded_upper or exceeded_lower
        exceeded_both = exceeded_upper and exceeded_lower
        
        # Verifica o fechamento
        close_within = (lower_strike <= final_price <= upper_strike)
        
        # Resultado financeiro
        #days_passed = (close_date - open_date).days  #dias corridos
        days_passed = len(pd.bdate_range(start=open_date, end=close_date)) -1   #dias uteis
        trade_result = final_profit
        trade_result_pct = (trade_result / total_premium) * 100
        
        # Adiciona aos resultados
        trade_info = {
            "open_date": open_date.isoformat(),
            "close_date": close_date.isoformat(),
            "opening_price": opening_price,
            "final_price": final_price,
            "upper_strike": upper_strike,
            "lower_strike": lower_strike,
            "premium_pct": premium_pct,
            "call_premium": call_premium,
            "put_premium": put_premium,
            "total_premium": total_premium,
            "final_call_value": call_value * num_contracts,
            "final_put_value": put_value * num_contracts,
            "option_cost": option_cost,
            "trade_result": trade_result,
            "trade_result_pct": trade_result_pct,
            "exceeded": exceeded,
            "exceeded_upper": exceeded_upper,
            "exceeded_lower": exceeded_lower,
            "exceeded_both": exceeded_both,
            "close_within": close_within,
            "early_exit": early_exit,
            "days_held": days_passed,
            "initial_volatility": opening_row["volatility"] * 100
        }
        
        trades.append(trade_info)
        
        results.append({
            "open_date": open_date.isoformat(),
            "close_date": close_date.isoformat(),
            "opening_price": opening_price,
            "final_price": final_price,
            "upper": upper_strike,
            "lower": lower_strike,
            "exceeded": exceeded,
            "exceeded_upper": exceeded_upper,
            "exceeded_lower": exceeded_lower,
            "exceeded_both": exceeded_both,
            "close_within": close_within,
            "trade_result": trade_result,
            "trade_result_pct": trade_result_pct,
            "early_exit": early_exit,
            "days_held": days_passed
        })
        
        # Avança para o próximo mês
        cur_month += 1
        if cur_month == 13:
            cur_month = 1
            cur_year += 1
    
    # Converte para DataFrame
    res_df = pd.DataFrame(results)
    trades_df = pd.DataFrame(trades)
    
    # Calcula as estatísticas
    total = len(res_df)
    if total == 0:
        return None
    
    never_exceeded = (~res_df["exceeded"]).sum()
    exceeded = res_df["exceeded"].sum()
    exceeded_within = res_df[(res_df["exceeded"]) & (res_df["close_within"])].shape[0]
    exceeded_within_both = res_df[(res_df["exceeded"]) & (res_df["close_within"]) & (res_df["exceeded_both"])].shape[0]
    exceeded_upper_only = res_df[(res_df["exceeded_upper"]) & (~res_df["exceeded_lower"])].shape[0]
    exceeded_lower_only = res_df[(res_df["exceeded_lower"]) & (~res_df["exceeded_upper"])].shape[0]
    exceeded_both_count = res_df["exceeded_both"].sum()
    closed_within = res_df["close_within"].sum()
    closed_outside = total - closed_within
    early_exits = res_df["early_exit"].sum()
    avg_days_held = res_df["days_held"].mean()
    
    # Estatísticas financeiras
    total_profit = trades_df["trade_result"].sum()
    avg_profit_per_trade = trades_df["trade_result"].mean()
    avg_profit_pct = trades_df["trade_result_pct"].mean()
    profitable_trades = (trades_df["trade_result"] > 0).sum()
    losing_trades = (trades_df["trade_result"] <= 0).sum()
    
    # Métricas de risco
    if profitable_trades > 0:
        avg_win = trades_df[trades_df["trade_result"] > 0]["trade_result"].mean()
    else:
        avg_win = 0
    
    if losing_trades > 0:
        avg_loss = trades_df[trades_df["trade_result"] <= 0]["trade_result"].mean()
    else:
        avg_loss = 0
    
    if avg_loss != 0:
        risk_reward = abs(avg_win / avg_loss)
    else:
        risk_reward = float("inf")
    
    win_rate = (profitable_trades / total) * 100 if total > 0 else 0
    
    # Resultados
    stats = {
        "total": total,
        "never_exceeded": never_exceeded,
        "never_exceeded_pct": (never_exceeded / total * 100) if total > 0 else 0,
        "exceeded": exceeded,
        "exceeded_pct": (exceeded / total * 100) if total > 0 else 0,
        "exceeded_within": exceeded_within,
        "exceeded_within_pct": (exceeded_within / exceeded * 100) if exceeded > 0 else 0,
        "exceeded_within_both": exceeded_within_both,
        "exceeded_within_both_pct": (exceeded_within_both / exceeded_within * 100) if exceeded_within > 0 else 0,
        "exceeded_upper_only": exceeded_upper_only,
        "exceeded_lower_only": exceeded_lower_only,
        "exceeded_both_count": exceeded_both_count,
        "closed_within": closed_within,
        "closed_within_pct": (closed_within / total * 100) if total > 0 else 0,
        "closed_outside": closed_outside,
        "closed_outside_pct": (closed_outside / total * 100) if total > 0 else 0,
        "early_exits": early_exits,
        "early_exits_pct": (early_exits / total * 100) if total > 0 else 0,
        "avg_days_held": avg_days_held,
        "total_profit": total_profit,
        "avg_profit_per_trade": avg_profit_per_trade,
        "avg_profit_pct": avg_profit_pct,
        "profitable_trades": profitable_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "risk_reward": risk_reward
    }
    
    return {
        "stats": stats,
        "trades": trades
    }
@app.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """Endpoint para executar o backtest."""
    try:
        # Validação dos anos
        if not 1 <= request.years <= 5:
            raise HTTPException(status_code=400, detail="O número de anos deve estar entre 1 e 5.")
        
        # Busca dados do yfinance
        df = get_yfinance_data(request.ticker, request.years)
        if df is None:
            raise HTTPException(status_code=404, detail=f"Não foi possível encontrar dados para {request.ticker} no yfinance.")
        
        # Executa o backtest
        results = backtest_strangle_yfinance(
            df, request.days_before, request.range_pct, request.premium_pct,
            request.num_contracts, request.early_profit_pct, request.friday_type
        )
        
        if results is None:
            raise HTTPException(status_code=500, detail="O backtest não pôde ser executado.")
        
        # CONVERSÃO PARA TIPOS NATIVOS
        for trade in results["trades"]:
            for k, v in trade.items():
                if isinstance(v, (np.integer, np.floating)):
                    trade[k] = v.item()
                elif isinstance(v, np.bool_):
                    trade[k] = bool(v)
        for k, v in results["stats"].items():
            if isinstance(v, (np.integer, np.floating)):
                results["stats"][k] = v.item()
            elif isinstance(v, np.bool_):
                results["stats"][k] = bool(v)

        # Retorna os resultados
        return BacktestResponse(
            success=True,
            message="Backtest executado com sucesso!",
            stats=results["stats"],
            trades=results["trades"]
        )
    except HTTPException as e:
        return BacktestResponse(success=False, message=e.detail)
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return BacktestResponse(success=False, message=f"Erro inesperado: {str(e)}")