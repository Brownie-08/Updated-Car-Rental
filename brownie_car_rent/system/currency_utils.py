"""
Currency conversion utilities for the car rental system.
Handles USD to NGN conversion for Paystack payments.
"""

import logging
import requests
from decimal import Decimal
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# Fallback exchange rate (as of recent data)
FALLBACK_USD_TO_NGN_RATE = Decimal('1650.00')  # 1 USD = 1650 NGN (approximate)

def get_usd_to_ngn_rate(use_api=True):
    """
    Get current USD to NGN exchange rate.
    
    Args:
        use_api (bool): Whether to try fetching from API or use fallback
    
    Returns:
        Decimal: Exchange rate (NGN per 1 USD)
    """
    
    # Check cache first
    cached_rate = cache.get('usd_to_ngn_rate')
    if cached_rate:
        logger.info(f"Using cached USD to NGN rate: {cached_rate}")
        return Decimal(str(cached_rate))
    
    if not use_api:
        logger.info(f"Using fallback USD to NGN rate: {FALLBACK_USD_TO_NGN_RATE}")
        return FALLBACK_USD_TO_NGN_RATE
    
    try:
        # Try to get rate from free API
        api_endpoints = [
            'https://api.exchangerate-api.com/v4/latest/USD',
            'https://api.fixer.io/latest?base=USD',  # Requires API key in production
        ]
        
        for api_url in api_endpoints:
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Different API response structures
                    rate = None
                    if 'rates' in data and 'NGN' in data['rates']:
                        rate = Decimal(str(data['rates']['NGN']))
                    
                    if rate and rate > 0:
                        # Cache rate for 1 hour
                        cache.set('usd_to_ngn_rate', float(rate), 3600)
                        logger.info(f"Fetched USD to NGN rate from API: {rate}")
                        return rate
                        
            except Exception as api_error:
                logger.warning(f"Failed to get rate from {api_url}: {str(api_error)}")
                continue
    
    except Exception as e:
        logger.error(f"Error fetching exchange rate: {str(e)}")
    
    # Use fallback rate
    logger.warning(f"Using fallback USD to NGN rate: {FALLBACK_USD_TO_NGN_RATE}")
    return FALLBACK_USD_TO_NGN_RATE


def convert_usd_to_ngn(usd_amount, use_api=True):
    """
    Convert USD amount to NGN.
    
    Args:
        usd_amount (Decimal or float): Amount in USD
        use_api (bool): Whether to use live exchange rate
    
    Returns:
        Decimal: Amount in NGN
    """
    try:
        usd_amount = Decimal(str(usd_amount))
        exchange_rate = get_usd_to_ngn_rate(use_api=use_api)
        ngn_amount = usd_amount * exchange_rate
        
        # Round to 2 decimal places
        ngn_amount = ngn_amount.quantize(Decimal('0.01'))
        
        logger.info(f"Converted ${usd_amount} USD to ₦{ngn_amount} NGN (rate: {exchange_rate})")
        return ngn_amount
        
    except Exception as e:
        logger.error(f"Error converting USD to NGN: {str(e)}")
        # Fallback calculation
        fallback_amount = Decimal(str(usd_amount)) * FALLBACK_USD_TO_NGN_RATE
        return fallback_amount.quantize(Decimal('0.01'))


def convert_ngn_to_kobo(ngn_amount):
    """
    Convert NGN amount to kobo (Paystack's base unit).
    
    Args:
        ngn_amount (Decimal or float): Amount in NGN
    
    Returns:
        int: Amount in kobo (NGN * 100)
    """
    try:
        ngn_amount = Decimal(str(ngn_amount))
        kobo_amount = ngn_amount * 100
        return int(kobo_amount)
    except Exception as e:
        logger.error(f"Error converting NGN to kobo: {str(e)}")
        return int(float(ngn_amount) * 100)


def convert_usd_to_kobo(usd_amount, use_api=True):
    """
    Convert USD amount directly to kobo for Paystack.
    
    Args:
        usd_amount (Decimal or float): Amount in USD
        use_api (bool): Whether to use live exchange rate
    
    Returns:
        int: Amount in kobo
    """
    ngn_amount = convert_usd_to_ngn(usd_amount, use_api=use_api)
    return convert_ngn_to_kobo(ngn_amount)


def format_currency_display(usd_amount, use_api=True):
    """
    Format currency for display showing both USD and NGN.
    
    Args:
        usd_amount (Decimal or float): Amount in USD
        use_api (bool): Whether to use live exchange rate
    
    Returns:
        dict: Formatted currency information
    """
    try:
        usd_amount = Decimal(str(usd_amount))
        ngn_amount = convert_usd_to_ngn(usd_amount, use_api=use_api)
        kobo_amount = convert_ngn_to_kobo(ngn_amount)
        exchange_rate = get_usd_to_ngn_rate(use_api=use_api)
        
        return {
            'usd_amount': f"${usd_amount:,.2f}",
            'ngn_amount': f"₦{ngn_amount:,.2f}",
            'kobo_amount': kobo_amount,
            'exchange_rate': f"1 USD = ₦{exchange_rate:,.2f}",
            'usd_numeric': float(usd_amount),
            'ngn_numeric': float(ngn_amount),
        }
    except Exception as e:
        logger.error(f"Error formatting currency display: {str(e)}")
        return {
            'usd_amount': f"${usd_amount:,.2f}",
            'ngn_amount': f"₦{float(usd_amount) * float(FALLBACK_USD_TO_NGN_RATE):,.2f}",
            'kobo_amount': int(float(usd_amount) * float(FALLBACK_USD_TO_NGN_RATE) * 100),
            'exchange_rate': f"1 USD = ₦{FALLBACK_USD_TO_NGN_RATE:,.2f} (fallback)",
            'usd_numeric': float(usd_amount),
            'ngn_numeric': float(usd_amount) * float(FALLBACK_USD_TO_NGN_RATE),
        }


# Configuration settings
class CurrencyConfig:
    """Currency conversion configuration"""
    
    # Whether to use live exchange rates or fallback
    USE_LIVE_RATES = getattr(settings, 'USE_LIVE_EXCHANGE_RATES', True)
    
    # Fallback rate if API fails
    FALLBACK_RATE = FALLBACK_USD_TO_NGN_RATE
    
    # Cache duration for exchange rates (in seconds)
    CACHE_DURATION = getattr(settings, 'EXCHANGE_RATE_CACHE_DURATION', 3600)  # 1 hour
    
    # Supported currencies
    BASE_CURRENCY = 'USD'
    TARGET_CURRENCY = 'NGN'
    PAYSTACK_CURRENCY = 'NGN'
    
    @classmethod
    def get_display_currencies(cls):
        """Get currencies for display"""
        return {
            'base': cls.BASE_CURRENCY,
            'target': cls.TARGET_CURRENCY,
            'paystack': cls.PAYSTACK_CURRENCY,
        }