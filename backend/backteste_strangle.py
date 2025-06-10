# backteste_strangle.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.stats import norm

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

def convert_numpy_types(obj):
    """Converte tipos NumPy/Pandas para tipos Python nativos."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, pd.Timestamp):
        return obj.strftime("%Y-%m-%d")
    elif isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d")
    elif pd.isna(obj):
        return None
    else:
        return obj

def rodar_backteste_strangle(
    df_dados,
    ticker,
    dias_antes_vencimento=5,
    percentual_distancia=5.0,
    percentual_premio=0.65,
    quantidade_opcoes=200,
    percentual_atingida=60,
    dia_vencimento="terceira"
):
    # ... (código anterior da função) ...

    while (cur_year < end.year) or (cur_year == end.year and cur_month <= end.month):
        expiration_date = nth_friday(cur_year, cur_month, friday_n)
        
        if expiration_date is None or expiration_date < start or expiration_date > end:
            cur_month += 1
            if cur_month == 13:
                cur_month = 1
                cur_year += 1
            continue
        
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
        
        before_expiration = business_days[business_days['Data'] < expiration_date].reset_index(drop=True)
        
        print(f"DEBUG: cur_year={cur_year}, cur_month={cur_month}")
        print(f"DEBUG: expiration_date={expiration_date}")
        print(f"DEBUG: business_days index: {business_days.index}")
        print(f"DEBUG: before_expiration index (reset): {before_expiration.index}")
        print(f"DEBUG: length before_expiration: {len(before_expiration)}")
        
        if before_expiration.empty or len(before_expiration) < dias_antes_vencimento:
            cur_month += 1
            if cur_month == 13:
                cur_month = 1
                cur_year += 1
            continue
        
        open_date = before_expiration.iloc[-dias_antes_vencimento]['Data']
        opening_row = df[df['Data'] == open_date].iloc[0]
        
        # ... (resto do código da função) ...
    """
    Executa o backteste de strangle intermediário.
    
    Args:
        df_dados: DataFrame com os dados históricos (colunas: date, open, high, low, close, volume)
        ticker: Símbolo da ação
        dias_antes_vencimento: Dias antes do vencimento para abrir posição
        percentual_distancia: % de distância para o strangle
        percentual_premio: % de prêmio recebido
        quantidade_opcoes: Número de contratos
        percentual_atingida: % atingida para saída antecipada
        dia_vencimento: "primeira" ou "terceira" sexta-feira
    
    Returns:
        dict: Resumo e tabela de resultados
    """
    
    # Converte os dados para o formato esperado pelo script original
    df = df_dados.copy()
    df = df.rename(columns={
        'date': 'Data',
        'close': 'Fechamento',
        'high': 'Máxima',
        'low': 'Mínima'
    })
    
    # Converte a coluna de data
    df['Data'] = pd.to_datetime(df['Data'])
    df = df.sort_values('Data')
    
    # Calcula a volatilidade histórica
    df["volatility"] = calculate_historical_volatility(df['Fechamento'])
    mean_volatility = df["volatility"].mean()
    if np.isnan(mean_volatility):
        mean_volatility = 0.25
    df["volatility"] = df["volatility"].fillna(mean_volatility)
    
    # Taxa de juros livre de risco
    risk_free_rate = 0.1075
    
    # Define qual sexta-feira usar
    friday_n = 1 if dia_vencimento.lower() == "primeira" else 3
    
    # Adiciona coluna de dia da semana
    df['weekday'] = df['Data'].dt.weekday
    business_days = df[df['weekday'] <= 4].copy()
    
    results = []
    trades = []
    
    start = df['Data'].min()
    end = df['Data'].max()
    
    # Para cada mês no período
    cur_year = start.year
    cur_month = start.month
    
    while (cur_year < end.year) or (cur_year == end.year and cur_month <= end.month):
        # Encontra a sexta-feira escolhida do mês
        expiration_date = nth_friday(cur_year, cur_month, friday_n)
        
        if expiration_date is None or expiration_date < start or expiration_date > end:
            cur_month += 1
            if cur_month == 13:
                cur_month = 1
                cur_year += 1
            continue
        
        # Garante que a data existe nos dados
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
        
        # Encontra a data de abertura
        before_expiration = business_days[business_days['Data'] < expiration_date]
        
        if before_expiration.empty or len(before_expiration) < dias_antes_vencimento:
            cur_month += 1
            if cur_month == 13:
                cur_month = 1
                cur_year += 1
            continue
        
        # Data de abertura
        open_date = before_expiration.iloc[-dias_antes_vencimento]['Data']
        opening_row = df[df['Data'] == open_date].iloc[0]
        opening_price = opening_row['Fechamento']
        upper_strike = opening_price * (1 + percentual_distancia/100)
        lower_strike = opening_price * (1 - percentual_distancia/100)
        
        # Calcula tempo até vencimento
        days_to_expiration = (expiration_date - open_date).days
        T_initial = days_to_expiration / 365.0
        
        # Volatilidade inicial
        initial_volatility = opening_row["volatility"]
        
        # Calcula prêmio usando Black-Scholes
        call_premium_bs = black_scholes(opening_price, upper_strike, T_initial, risk_free_rate, initial_volatility, "call")
        put_premium_bs = black_scholes(opening_price, lower_strike, T_initial, risk_free_rate, initial_volatility, "put")
        
        # Ajusta o prêmio
        desired_premium = opening_price * percentual_premio / 100
        total_premium_bs = call_premium_bs + put_premium_bs
        
        adjustment_factor = 1.0
        if total_premium_bs > 0:
            adjustment_factor = (desired_premium * 2) / total_premium_bs
        
        call_premium = call_premium_bs * adjustment_factor
        put_premium = put_premium_bs * adjustment_factor
        total_premium = (call_premium + put_premium) * quantidade_opcoes
        
        # Período entre abertura e vencimento
        period_mask = (df['Data'] > open_date) & (df['Data'] <= expiration_date)
        period = df.loc[period_mask]
        
        if period.empty:
            cur_month += 1
            if cur_month == 13:
                cur_month = 1
                cur_year += 1
            continue
        
        # Valor alvo para saída antecipada
        early_exit_target = total_premium * percentual_atingida / 100
        
        # Variáveis para rastrear saída antecipada
        early_exit = False
        early_exit_date = None
        early_exit_price = None
        option_values = []
        
        # Analisar cada dia para verificar saída antecipada
        for idx, day in period.iterrows():
            current_date = day['Data']
            current_price = day['Fechamento']
            current_volatility = day["volatility"]
            
            T_remaining = (expiration_date - current_date).days / 365.0
            
            current_call_value = black_scholes(current_price, upper_strike, T_remaining, risk_free_rate, current_volatility, "call")
            current_put_value = black_scholes(current_price, lower_strike, T_remaining, risk_free_rate, current_volatility, "put")
            
            current_call_value *= adjustment_factor
            current_put_value *= adjustment_factor
            
            current_option_cost = (current_call_value + current_put_value) * quantidade_opcoes
            current_profit = total_premium - current_option_cost
            
            option_values.append({
                "date": current_date,
                "price": current_price,
                "call_value": current_call_value,
                "put_value": current_put_value,
                "total_cost": current_option_cost,
                "profit": current_profit,
                "profit_pct": (current_profit / total_premium) * 100
            })
            
            if current_profit >= early_exit_target:
                early_exit = True
                early_exit_date = current_date
                early_exit_price = current_price
                break
        
        # Calcula resultado final
        if early_exit:
            period_until_exit = df[(df['Data'] > open_date) & (df['Data'] <= early_exit_date)]
            max_price = period_until_exit['Máxima'].max()
            min_price = period_until_exit['Mínima'].min()
            final_price = early_exit_price
            close_date = early_exit_date
            
            last_option_values = option_values[-1]
            call_value = last_option_values["call_value"]
            put_value = last_option_values["put_value"]
            option_cost = last_option_values["total_cost"]
            final_profit = last_option_values["profit"]
        else:
            max_price = period['Máxima'].max()
            min_price = period['Mínima'].min()
            final_price = period.iloc[-1]['Fechamento']
            close_date = expiration_date
            
            call_value = max(0, final_price - upper_strike)
            put_value = max(0, lower_strike - final_price)
            option_cost = (call_value + put_value) * quantidade_opcoes
            final_profit = total_premium - option_cost
        
        # Verifica se ultrapassou o range
        exceeded_upper = max_price > upper_strike
        exceeded_lower = min_price < lower_strike
        exceeded = exceeded_upper or exceeded_lower
        exceeded_both = exceeded_upper and exceeded_lower
        
        close_within = (lower_strike <= final_price <= upper_strike)
        
        days_passed = (close_date - open_date).days
        trade_result = final_profit
        trade_result_pct = (trade_result / total_premium) * 100
        
        # Adiciona aos resultados - CONVERTENDO TODOS OS TIPOS NUMPY
        trade_info = {
            "open_date": convert_numpy_types(open_date),
            "close_date": convert_numpy_types(close_date),
            "opening_price": convert_numpy_types(round(opening_price, 2)),
            "final_price": convert_numpy_types(round(final_price, 2)),
            "upper_strike": convert_numpy_types(round(upper_strike, 2)),
            "lower_strike": convert_numpy_types(round(lower_strike, 2)),
            "premium_pct": convert_numpy_types(percentual_premio),
            "call_premium": convert_numpy_types(round(call_premium, 2)),
            "put_premium": convert_numpy_types(round(put_premium, 2)),
            "total_premium": convert_numpy_types(round(total_premium, 2)),
            "final_call_value": convert_numpy_types(round(call_value * quantidade_opcoes, 2)),
            "final_put_value": convert_numpy_types(round(put_value * quantidade_opcoes, 2)),
            "option_cost": convert_numpy_types(round(option_cost, 2)),
            "trade_result": convert_numpy_types(round(trade_result, 2)),
            "trade_result_pct": convert_numpy_types(round(trade_result_pct, 2)),
            "exceeded": convert_numpy_types(exceeded),
            "exceeded_upper": convert_numpy_types(exceeded_upper),
            "exceeded_lower": convert_numpy_types(exceeded_lower),
            "exceeded_both": convert_numpy_types(exceeded_both),
            "close_within": convert_numpy_types(close_within),
            "early_exit": convert_numpy_types(early_exit),
            "days_held": convert_numpy_types(days_passed),
            "initial_volatility": convert_numpy_types(round(initial_volatility * 100, 2))
        }
        
        trades.append(trade_info)
        
        # Avança para o próximo mês
        cur_month += 1
        if cur_month == 13:
            cur_month = 1
            cur_year += 1
    
    # Calcula estatísticas
    if not trades:
        return {
            "resumo": {"erro": "Nenhum período válido encontrado para análise"},
            "tabela": []
        }
    
    trades_df = pd.DataFrame(trades)
    total = len(trades_df)
    
    never_exceeded = int((~trades_df["exceeded"]).sum())
    exceeded = int(trades_df["exceeded"].sum())
    exceeded_within = int(trades_df[(trades_df["exceeded"]) & (trades_df["close_within"])].shape[0])
    exceeded_within_both = int(trades_df[(trades_df["exceeded"]) & (trades_df["close_within"]) & (trades_df["exceeded_both"])].shape[0])
    exceeded_upper_only = int(trades_df[(trades_df["exceeded_upper"]) & (~trades_df["exceeded_lower"])].shape[0])
    exceeded_lower_only = int(trades_df[(trades_df["exceeded_lower"]) & (~trades_df["exceeded_upper"])].shape[0])
    exceeded_both_count = int(trades_df["exceeded_both"].sum())
    closed_within = int(trades_df["close_within"].sum())
    closed_outside = total - closed_within
    early_exits = int(trades_df["early_exit"].sum())
    avg_days_held = float(trades_df["days_held"].mean())
    
    # Estatísticas financeiras
    total_profit = float(trades_df["trade_result"].sum())
    avg_profit_per_trade = float(trades_df["trade_result"].mean())
    avg_profit_pct = float(trades_df["trade_result_pct"].mean())
    profitable_trades = int((trades_df["trade_result"] > 0).sum())
    losing_trades = int((trades_df["trade_result"] <= 0).sum())
    
    if profitable_trades > 0:
        avg_win = float(trades_df[trades_df["trade_result"] > 0]["trade_result"].mean())
    else:
        avg_win = 0.0
    
    if losing_trades > 0:
        avg_loss = float(trades_df[trades_df["trade_result"] <= 0]["trade_result"].mean())
    else:
        avg_loss = 0.0
    
    if avg_loss != 0:
        risk_reward = float(abs(avg_win / avg_loss))
    else:
        risk_reward = float("inf")
    
    win_rate = float((profitable_trades / total) * 100) if total > 0 else 0.0
    
    # Monta o resumo - CONVERTENDO TODOS OS TIPOS
    resumo = {
        "ticker": str(ticker),
        "total_operacoes": int(total),
        "dias_antes_vencimento": int(dias_antes_vencimento),
        "percentual_distancia": float(percentual_distancia),
        "percentual_premio": float(percentual_premio),
        "quantidade_opcoes": int(quantidade_opcoes),
        "percentual_atingida": int(percentual_atingida),
        "dia_vencimento": str(dia_vencimento),
        "never_exceeded": never_exceeded,
        "never_exceeded_pct": round((never_exceeded / total * 100), 2),
        "exceeded": exceeded,
        "exceeded_pct": round((exceeded / total * 100), 2),
        "exceeded_within": exceeded_within,
        "exceeded_within_pct": round((exceeded_within / exceeded * 100), 2) if exceeded > 0 else 0.0,
        "exceeded_within_both": exceeded_within_both,
        "exceeded_within_both_pct": round((exceeded_within_both / exceeded_within * 100), 2) if exceeded_within > 0 else 0.0,
        "exceeded_upper_only": exceeded_upper_only,
        "exceeded_lower_only": exceeded_lower_only,
        "exceeded_both_count": exceeded_both_count,
        "closed_within": closed_within,
        "closed_within_pct": round((closed_within / total * 100), 2),
        "closed_outside": closed_outside,
        "closed_outside_pct": round((closed_outside / total * 100), 2),
        "early_exits": early_exits,
        "early_exits_pct": round((early_exits / total * 100), 2),
        "avg_days_held": round(avg_days_held, 1),
        "total_profit": round(total_profit, 2),
        "avg_profit_per_trade": round(avg_profit_per_trade, 2),
        "avg_profit_pct": round(avg_profit_pct, 2),
        "profitable_trades": profitable_trades,
        "losing_trades": losing_trades,
        "win_rate": round(win_rate, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "risk_reward": round(risk_reward, 2) if risk_reward != float("inf") else "∞"
    }
    
    return {
        "resumo": resumo,
        "tabela": trades
    }