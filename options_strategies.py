import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from modules.options_analysis import get_options_chain
import streamlit as st

class OptionsStrategy:
    def __init__(self, symbol):
        self.symbol = symbol
        
    def get_expiry_dates(self, min_days=30, max_days=60):
        """Get valid expiration dates within range"""
        options_df, expiry_dates = get_options_chain(self.symbol, num_expiries=12)
        
        valid_dates = []
        for date in expiry_dates:
            days_to_expiry = (pd.to_datetime(date) - pd.Timestamp.now()).days
            if min_days <= days_to_expiry <= max_days:
                valid_dates.append(date)
                
        return valid_dates

    def find_strike_prices(self, current_price, width_percentage=0.05):
        """Find appropriate strike prices around current price"""
        options_df, _ = get_options_chain(self.symbol, num_expiries=1)
        
        lower_bound = current_price * (1 - width_percentage)
        upper_bound = current_price * (1 + width_percentage)
        
        valid_strikes = options_df[
            (options_df['strike'] >= lower_bound) &
            (options_df['strike'] <= upper_bound)
        ]['strike'].unique()
        
        return sorted(valid_strikes)

    def create_vertical_spread(self, spread_type, expiry_date, current_price, width=0.05):
        """Create a bull call spread or bear put spread"""
        options_df = get_options_chain(self.symbol, num_expiries=1)[0]
        options_df = options_df[options_df['expiration'] == expiry_date]
        
        strikes = self.find_strike_prices(current_price, width)
        if len(strikes) < 2:
            return None
            
        if spread_type == "bull_call":
            # Bull Call Spread
            long_strike = strikes[0]  # Lower strike (buy)
            short_strike = strikes[-1]  # Higher strike (sell)
            
            long_call = options_df[
                (options_df['strike'] == long_strike) &
                (options_df['optionType'] == 'CALL')
            ].iloc[0]
            
            short_call = options_df[
                (options_df['strike'] == short_strike) &
                (options_df['optionType'] == 'CALL')
            ].iloc[0]
            
            max_loss = (long_call['lastPrice'] - short_call['lastPrice']) * 100
            max_profit = (short_strike - long_strike - max_loss/100) * 100
            
            return {
                'strategy': 'bull_call_spread',
                'long_option': {
                    'type': 'CALL',
                    'strike': long_strike,
                    'premium': long_call['lastPrice']
                },
                'short_option': {
                    'type': 'CALL',
                    'strike': short_strike,
                    'premium': short_call['lastPrice']
                },
                'expiry': expiry_date,
                'max_loss': max_loss,
                'max_profit': max_profit,
                'break_even': long_strike + max_loss/100
            }
            
        elif spread_type == "bear_put":
            # Bear Put Spread
            long_strike = strikes[-1]  # Higher strike (buy)
            short_strike = strikes[0]  # Lower strike (sell)
            
            long_put = options_df[
                (options_df['strike'] == long_strike) &
                (options_df['optionType'] == 'PUT')
            ].iloc[0]
            
            short_put = options_df[
                (options_df['strike'] == short_strike) &
                (options_df['optionType'] == 'PUT')
            ].iloc[0]
            
            max_loss = (long_put['lastPrice'] - short_put['lastPrice']) * 100
            max_profit = (long_strike - short_strike - max_loss/100) * 100
            
            return {
                'strategy': 'bear_put_spread',
                'long_option': {
                    'type': 'PUT',
                    'strike': long_strike,
                    'premium': long_put['lastPrice']
                },
                'short_option': {
                    'type': 'PUT',
                    'strike': short_strike,
                    'premium': short_put['lastPrice']
                },
                'expiry': expiry_date,
                'max_loss': max_loss,
                'max_profit': max_profit,
                'break_even': long_strike - max_loss/100
            }

    def create_iron_condor(self, expiry_date, current_price, width=0.05):
        """Create an iron condor strategy"""
        options_df = get_options_chain(self.symbol, num_expiries=1)[0]
        options_df = options_df[options_df['expiration'] == expiry_date]
        
        strikes = self.find_strike_prices(current_price, width)
        if len(strikes) < 4:
            return None
            
        # Iron Condor requires 4 strikes
        put_strikes = strikes[:2]  # Lower strikes for put spread
        call_strikes = strikes[-2:]  # Higher strikes for call spread
        
        # Put spread (sell higher strike, buy lower strike)
        long_put = options_df[
            (options_df['strike'] == put_strikes[0]) &
            (options_df['optionType'] == 'PUT')
        ].iloc[0]
        
        short_put = options_df[
            (options_df['strike'] == put_strikes[1]) &
            (options_df['optionType'] == 'PUT')
        ].iloc[0]
        
        # Call spread (sell lower strike, buy higher strike)
        short_call = options_df[
            (options_df['strike'] == call_strikes[0]) &
            (options_df['optionType'] == 'CALL')
        ].iloc[0]
        
        long_call = options_df[
            (options_df['strike'] == call_strikes[1]) &
            (options_df['optionType'] == 'CALL')
        ].iloc[0]
        
        # Calculate max profit/loss
        net_credit = (short_put['lastPrice'] + short_call['lastPrice'] - 
                     long_put['lastPrice'] - long_call['lastPrice'])
        max_profit = net_credit * 100
        max_loss = min(
            call_strikes[1] - call_strikes[0],
            put_strikes[1] - put_strikes[0]
        ) * 100 - max_profit
        
        return {
            'strategy': 'iron_condor',
            'put_spread': {
                'long': {
                    'strike': put_strikes[0],
                    'premium': long_put['lastPrice']
                },
                'short': {
                    'strike': put_strikes[1],
                    'premium': short_put['lastPrice']
                }
            },
            'call_spread': {
                'short': {
                    'strike': call_strikes[0],
                    'premium': short_call['lastPrice']
                },
                'long': {
                    'strike': call_strikes[1],
                    'premium': long_call['lastPrice']
                }
            },
            'expiry': expiry_date,
            'max_loss': max_loss,
            'max_profit': max_profit,
            'break_even_lower': put_strikes[1] - net_credit,
            'break_even_upper': call_strikes[0] + net_credit
        }

    def create_butterfly(self, expiry_date, current_price, width=0.05):
        """Create a butterfly spread strategy"""
        options_df = get_options_chain(self.symbol, num_expiries=1)[0]
        options_df = options_df[options_df['expiration'] == expiry_date]
        
        strikes = self.find_strike_prices(current_price, width)
        if len(strikes) < 3:
            return None
            
        # Butterfly needs 3 equidistant strikes
        lower_strike = strikes[0]
        middle_strike = strikes[len(strikes)//2]
        upper_strike = strikes[-1]
        
        # Buy lower strike call
        lower_call = options_df[
            (options_df['strike'] == lower_strike) &
            (options_df['optionType'] == 'CALL')
        ].iloc[0]
        
        # Sell 2 middle strike calls
        middle_call = options_df[
            (options_df['strike'] == middle_strike) &
            (options_df['optionType'] == 'CALL')
        ].iloc[0]
        
        # Buy upper strike call
        upper_call = options_df[
            (options_df['strike'] == upper_strike) &
            (options_df['optionType'] == 'CALL')
        ].iloc[0]
        
        # Calculate max profit/loss
        net_debit = (lower_call['lastPrice'] - 2 * middle_call['lastPrice'] + 
                    upper_call['lastPrice'])
        max_loss = net_debit * 100
        max_profit = (middle_strike - lower_strike) * 100 - max_loss
        
        return {
            'strategy': 'butterfly',
            'lower_call': {
                'strike': lower_strike,
                'premium': lower_call['lastPrice']
            },
            'middle_calls': {
                'strike': middle_strike,
                'premium': middle_call['lastPrice']
            },
            'upper_call': {
                'strike': upper_strike,
                'premium': upper_call['lastPrice']
            },
            'expiry': expiry_date,
            'max_loss': max_loss,
            'max_profit': max_profit,
            'break_even_lower': lower_strike + net_debit,
            'break_even_upper': upper_strike - net_debit
        }

    def select_best_strategy(self, current_price, technicals, options_flow):
        """Select the best options strategy based on market conditions"""
        expiry_dates = self.get_expiry_dates()
        if not expiry_dates:
            return None
            
        expiry_date = expiry_dates[0]
        strategies = []
        
        # Market conditions analysis
        is_trending = technicals['uptrend'] or technicals['near_support'] or technicals['near_resistance']
        is_volatile = technicals['rsi'] > 70 or technicals['rsi'] < 30
        is_bullish = (technicals['uptrend'] and technicals['near_support'] and 
                     options_flow['bullish_flow'])
        is_bearish = (not technicals['uptrend'] and technicals['near_resistance'] and 
                     not options_flow['bullish_flow'])
        
        # Strategy selection based on market conditions
        if is_bullish and not is_volatile:
            # Bullish trend - Use bull call spread
            strategy = self.create_vertical_spread("bull_call", expiry_date, current_price)
            if strategy:
                strategies.append(strategy)
                
        elif is_bearish and not is_volatile:
            # Bearish trend - Use bear put spread
            strategy = self.create_vertical_spread("bear_put", expiry_date, current_price)
            if strategy:
                strategies.append(strategy)
                
        elif is_volatile:
            # High volatility - Use butterfly spread
            strategy = self.create_butterfly(expiry_date, current_price)
            if strategy:
                strategies.append(strategy)
                
        elif not is_trending:
            # Range-bound - Use iron condor
            strategy = self.create_iron_condor(expiry_date, current_price)
            if strategy:
                strategies.append(strategy)
        
        # Select the strategy with the best risk/reward ratio
        if strategies:
            best_strategy = max(strategies, 
                              key=lambda x: abs(x['max_profit']/x['max_loss']) 
                              if x['max_loss'] != 0 else 0)
            return best_strategy
            
        return None

    def execute_strategy(self, strategy_details):
        """Execute the selected options strategy"""
        if not strategy_details:
            return None
            
        trade = {
            'symbol': self.symbol,
            'type': 'options_strategy',
            'strategy_type': strategy_details['strategy'],
            'entry_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'expiry': strategy_details['expiry'],
            'max_loss': strategy_details['max_loss'],
            'max_profit': strategy_details['max_profit'],
            'status': 'open',
            'legs': []
        }
        
        # Add strategy-specific details
        if strategy_details['strategy'] in ['bull_call_spread', 'bear_put_spread']:
            trade['legs'].extend([
                {
                    'type': strategy_details['long_option']['type'],
                    'action': 'buy',
                    'strike': strategy_details['long_option']['strike'],
                    'premium': strategy_details['long_option']['premium']
                },
                {
                    'type': strategy_details['short_option']['type'],
                    'action': 'sell',
                    'strike': strategy_details['short_option']['strike'],
                    'premium': strategy_details['short_option']['premium']
                }
            ])
            
        elif strategy_details['strategy'] == 'iron_condor':
            trade['legs'].extend([
                {
                    'type': 'PUT',
                    'action': 'buy',
                    'strike': strategy_details['put_spread']['long']['strike'],
                    'premium': strategy_details['put_spread']['long']['premium']
                },
                {
                    'type': 'PUT',
                    'action': 'sell',
                    'strike': strategy_details['put_spread']['short']['strike'],
                    'premium': strategy_details['put_spread']['short']['premium']
                },
                {
                    'type': 'CALL',
                    'action': 'sell',
                    'strike': strategy_details['call_spread']['short']['strike'],
                    'premium': strategy_details['call_spread']['short']['premium']
                },
                {
                    'type': 'CALL',
                    'action': 'buy',
                    'strike': strategy_details['call_spread']['long']['strike'],
                    'premium': strategy_details['call_spread']['long']['premium']
                }
            ])
            
        elif strategy_details['strategy'] == 'butterfly':
            trade['legs'].extend([
                {
                    'type': 'CALL',
                    'action': 'buy',
                    'strike': strategy_details['lower_call']['strike'],
                    'premium': strategy_details['lower_call']['premium']
                },
                {
                    'type': 'CALL',
                    'action': 'sell',
                    'strike': strategy_details['middle_calls']['strike'],
                    'premium': strategy_details['middle_calls']['premium'],
                    'quantity': 2
                },
                {
                    'type': 'CALL',
                    'action': 'buy',
                    'strike': strategy_details['upper_call']['strike'],
                    'premium': strategy_details['upper_call']['premium']
                }
            ])
            
        return trade
