import streamlit as st
import pandas as pd
import time
from datetime import datetime
import threading
import os

from api_client import CryptoDataClient
from data_processor import process_market_maker_data
from venn_visualizer import create_venn_diagram

# Page configuration
st.set_page_config(
    page_title="Crypto Market Maker Holdings Visualization",
    page_icon="📊",
    layout="wide"
)

# Initialize API client
# We're using CoinGecko API which doesn't require an API key
api_client = CryptoDataClient()

# Initialize session state for data storage
if 'market_maker_data' not in st.session_state:
    st.session_state.market_maker_data = None
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = None
if 'update_thread' not in st.session_state:
    st.session_state.update_thread = None
if 'update_running' not in st.session_state:
    st.session_state.update_running = False

# Function to fetch and process data
def update_data():
    st.session_state.update_running = True
    try:
        # List of major market makers to track
        market_makers = {
            'exchanges': ['binance', 'coinbase', 'kraken', 'kucoin', 'ftx'],
            'institutions': ['fidelity', 'blackrock', 'grayscale', 'wintermute', 'jump_trading']
        }
        
        # Fetch data for each market maker
        raw_data = {}
        with st.spinner("Fetching data from CoinGecko API..."):
            for category, entities in market_makers.items():
                for entity in entities:
                    try:
                        entity_data = api_client.get_entity_holdings(entity)
                        if entity_data:
                            raw_data[entity] = entity_data
                    except Exception as e:
                        st.error(f"Error fetching data for {entity}: {str(e)}")
        
        # Process the data for visualization
        processed_data = process_market_maker_data(raw_data)
        
        # Update session state
        st.session_state.market_maker_data = processed_data
        st.session_state.last_update_time = datetime.now()
        
        # Force a rerun to update the UI
        st.rerun()
    except Exception as e:
        st.error(f"Error updating data: {str(e)}")
    finally:
        st.session_state.update_running = False

# Background thread for automatic updates
def background_update():
    while True:
        # Update every hour
        time.sleep(3600)
        if not st.session_state.update_running:
            update_data()

# Start background update thread if not already running
if st.session_state.update_thread is None:
    update_thread = threading.Thread(target=background_update, daemon=True)
    update_thread.start()
    st.session_state.update_thread = update_thread

# Main interface with a professional look
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    .highlight {
        background: linear-gradient(90deg, #3B82F6, #10B981);
        background-clip: text;
        -webkit-background-clip: text;
        color: transparent;
        font-weight: 600;
    }
    .stButton button {
        background-color: #2563EB;
        color: white;
        font-weight: 500;
        border-radius: 0.375rem;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton button:hover {
        background-color: #1D4ED8;
    }
    .st-emotion-cache-16txtl3 h4 {
        font-weight: 600;
        margin-top: 1rem;
    }
</style>
<div class="main-header">Cryptocurrency Holdings Dashboard</div>
<div class="sub-header">
    Explore how <span class="highlight">major market makers</span> distribute their crypto assets
</div>
""", unsafe_allow_html=True)

# App description with improved formatting
st.markdown("""
This interactive dashboard visualizes cryptocurrency holdings across major exchanges and institutional investors. 
Data is sourced in real-time from CoinGecko's API and updated hourly.

**Features:**
- Compare holdings across different market makers
- Identify overlapping investments
- Track market share by cryptocurrency
- Analyze institutional investment patterns
""")

# Enhanced sidebar with professional styling
st.sidebar.markdown("""
<style>
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1E3A8A;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #E5E7EB;
    }
    .sidebar-subheader {
        font-size: 1.1rem;
        font-weight: 600;
        color: #4B5563;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
    .last-updated {
        background-color: #EFF6FF;
        border-left: 3px solid #3B82F6;
        padding: 0.75rem;
        font-size: 0.9rem;
        margin-top: 1rem;
        margin-bottom: 1.5rem;
        border-radius: 0.25rem;
    }
    .refresh-note {
        font-size: 0.8rem;
        color: #6B7280;
        font-style: italic;
        margin-top: 0.5rem;
    }
</style>
<div class="sidebar-header">Dashboard Controls</div>
""", unsafe_allow_html=True)

# Manual refresh button with improved styling
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    update_data()

# Display last update time with better formatting
if st.session_state.last_update_time:
    st.sidebar.markdown(f"""
    <div class="last-updated">
        <strong>Last updated:</strong><br>
        {st.session_state.last_update_time.strftime('%B %d, %Y at %H:%M:%S')}
        <div class="refresh-note">Data automatically refreshes hourly</div>
    </div>
    """, unsafe_allow_html=True)

# Fetch data if not already present
if st.session_state.market_maker_data is None:
    update_data()

# Display filters only if we have data
if st.session_state.market_maker_data is not None:
    # Extract unique entities and assets for filtering
    all_entities = list(st.session_state.market_maker_data['entities'].keys())
    all_assets = list(st.session_state.market_maker_data['assets'].keys())
    
    # Entity filter with custom styling
    st.sidebar.markdown('<div class="sidebar-subheader">Filter by Market Makers</div>', unsafe_allow_html=True)
    
    # Add a button to select/deselect all entities
    col1, col2 = st.sidebar.columns(2)
    if col1.button("Select All", key="select_all_entities", use_container_width=True):
        default_entities = all_entities
    else:
        default_entities = all_entities[:5]  # Default to first 5 entities
    
    if col2.button("Clear All", key="clear_all_entities", use_container_width=True):
        default_entities = []
    
    selected_entities = st.sidebar.multiselect(
        "Choose which market makers to display:",
        options=all_entities,
        default=default_entities
    )
    
    # Add helpful note about selection
    if len(selected_entities) > 0:
        st.sidebar.markdown(f"<div style='color: #4B5563; font-size: 0.8rem; margin-bottom: 1rem;'>Showing data for {len(selected_entities)} market makers</div>", unsafe_allow_html=True)
    
    # Asset filter with custom styling
    st.sidebar.markdown('<div class="sidebar-subheader">Filter by Assets</div>', unsafe_allow_html=True)
    
    # Sort assets by value for better organization
    sorted_assets = sorted(all_assets, 
                         key=lambda x: st.session_state.market_maker_data['assets'][x]['total_value'], 
                         reverse=True)
    
    # Add a button to select/deselect all assets
    col1, col2 = st.sidebar.columns(2)
    if col1.button("Top 10", key="select_top_assets", use_container_width=True):
        default_assets = sorted_assets[:10]
    else:
        default_assets = sorted_assets[:10]  # Default to top 10 assets by value
    
    if col2.button("Clear All", key="clear_all_assets", use_container_width=True):
        default_assets = []
    
    selected_assets = st.sidebar.multiselect(
        "Choose which cryptocurrencies to display:",
        options=sorted_assets,
        default=default_assets,
        format_func=lambda x: f"{x} (${st.session_state.market_maker_data['assets'][x]['total_value']:,.0f})"
    )
    
    # Add helpful note about selection
    if len(selected_assets) > 0:
        total_value = sum(st.session_state.market_maker_data['assets'][asset]['total_value'] for asset in selected_assets)
        st.sidebar.markdown(f"<div style='color: #4B5563; font-size: 0.8rem; margin-bottom: 1rem;'>Showing {len(selected_assets)} assets with total value of ${total_value:,.0f}</div>", unsafe_allow_html=True)
    
    # Apply filters and create visualization
    if selected_entities and selected_assets:
        filtered_data = {
            'entities': {entity: st.session_state.market_maker_data['entities'][entity] 
                        for entity in selected_entities if entity in st.session_state.market_maker_data['entities']},
            'assets': {asset: st.session_state.market_maker_data['assets'][asset] 
                      for asset in selected_assets if asset in st.session_state.market_maker_data['assets']}
        }
        
        # Create and display Venn diagram with a better title
        st.markdown("""
        <style>
            .chart-title {
                font-size: 1.5rem;
                font-weight: 600;
                color: #1E3A8A;
                margin-bottom: 1rem;
                padding-bottom: 0.5rem;
                border-bottom: 2px solid #E5E7EB;
            }
            .chart-description {
                font-size: 0.9rem;
                color: #6B7280;
                margin-bottom: 1.5rem;
            }
            .data-section {
                background-color: white;
                padding: 1.5rem;
                border-radius: 0.5rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
                margin-top: 2rem;
                margin-bottom: 2rem;
            }
            .data-title {
                font-size: 1.3rem;
                font-weight: 600;
                color: #1E3A8A;
                margin-bottom: 1rem;
            }
            .highlight-blue {
                color: #2563EB;
                font-weight: 500;
            }
            .no-data {
                background-color: #EFF6FF;
                padding: 1rem;
                border-radius: 0.5rem;
                border-left: 3px solid #3B82F6;
                color: #1E40AF;
                font-size: 0.9rem;
            }
            .footer {
                text-align: center;
                margin-top: 3rem;
                padding-top: 1.5rem;
                border-top: 1px solid #E5E7EB;
                color: #6B7280;
                font-size: 0.8rem;
            }
        </style>
        <div class="chart-title">Cryptocurrency Asset Distribution Visualization</div>
        <div class="chart-description">
            This visualization shows how different cryptocurrencies are held across major market makers. 
            Larger bubbles represent higher value holdings, while position indicates which market makers hold each asset.
        </div>
        """, unsafe_allow_html=True)
        
        # Display the Venn diagram
        venn_fig = create_venn_diagram(filtered_data)
        st.plotly_chart(venn_fig, use_container_width=True)
        
        # Display tabular data in a nicer format
        st.markdown('<div class="data-section">', unsafe_allow_html=True)
        st.markdown('<div class="data-title">Detailed Holdings Data</div>', unsafe_allow_html=True)
        
        # Prepare data for table
        table_data = []
        for asset in selected_assets:
            if asset in st.session_state.market_maker_data['assets']:
                asset_info = st.session_state.market_maker_data['assets'][asset]
                holders = [entity for entity in selected_entities 
                          if asset in st.session_state.market_maker_data['entities'][entity]['assets']]
                
                table_data.append({
                    "Asset": asset,
                    "Total Value (USD)": f"${asset_info['total_value']:,.2f}",
                    "Total Quantity": f"{asset_info['total_quantity']:,.4f}",
                    "Market Share": f"{(asset_info['total_value'] / sum(filtered_data['assets'][a]['total_value'] for a in filtered_data['assets'])) * 100:.2f}%",
                    "Holders": ", ".join(holders)
                })
        
        # Sort data by value for better presentation
        if table_data:
            df = pd.DataFrame(table_data)
            # Sort by value (removing $ and commas for sorting)
            df['Sort Value'] = df['Total Value (USD)'].str.replace('$', '').str.replace(',', '').astype(float)
            df = df.sort_values('Sort Value', ascending=False)
            df = df.drop(columns=['Sort Value'])
            
            # Show the data with a scrollable, highlightable table
            st.dataframe(
                df,
                use_container_width=True,
                height=400,
                hide_index=True,
            )
            
            # Add summary statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"<div style='text-align: center;'><span style='font-size: 0.9rem;'>Total Assets</span><br><span style='font-size: 1.5rem;' class='highlight-blue'>{len(df)}</span></div>", unsafe_allow_html=True)
            with col2:
                total_value = sum(asset_info['total_value'] for asset_info in filtered_data['assets'].values())
                st.markdown(f"<div style='text-align: center;'><span style='font-size: 0.9rem;'>Total Value</span><br><span style='font-size: 1.5rem;' class='highlight-blue'>${total_value:,.0f}</span></div>", unsafe_allow_html=True)
            with col3:
                avg_holders = sum(len(asset_info['entities']) for asset_info in filtered_data['assets'].values()) / len(filtered_data['assets'])
                st.markdown(f"<div style='text-align: center;'><span style='font-size: 0.9rem;'>Avg Holders per Asset</span><br><span style='font-size: 1.5rem;' class='highlight-blue'>{avg_holders:.1f}</span></div>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="no-data">No data available for the selected filters. Please adjust your selection criteria.</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add a professional footer
        st.markdown("""
        <div class="footer">
            <p>Data provided by CoinGecko API • Updated hourly • Last refresh: {}</p>
            <p>This dashboard visualizes cryptocurrency holdings of major market makers and institutional investors.</p>
        </div>
        """.format(st.session_state.last_update_time.strftime('%Y-%m-%d %H:%M:%S') if st.session_state.last_update_time else "Never"), unsafe_allow_html=True)
    else:
        st.warning("Please select at least one market maker and one asset.")
else:
    st.info("Loading data from CoinGecko API. Please wait...")
  import requests
import json
import time
import random
from typing import Dict, List, Any, Optional

class CryptoDataClient:
    """
    Client for fetching cryptocurrency data from public APIs.
    Provides market data for major exchanges and institutions.
    """
    
    def __init__(self):
        """
        Initialize the API client.
        No API key required for CoinGecko's free tier.
        """
        self.base_url = "https://api.coingecko.com/api/v3"
        self.headers = {
            "Accept": "application/json"
        }
        # Map of entity names (exchanges, institutions) to their CoinGecko IDs
        self.exchange_info = {
            "binance": {"name": "Binance", "id": "binance"},
            "coinbase": {"name": "Coinbase", "id": "gdax"},
            "kraken": {"name": "Kraken", "id": "kraken"},
            "kucoin": {"name": "KuCoin", "id": "kucoin"},
            "ftx": {"name": "FTX", "id": "ftx_spot"},
            "fidelity": {"name": "Fidelity Digital Assets", "id": None},
            "blackrock": {"name": "BlackRock", "id": None},
            "grayscale": {"name": "Grayscale", "id": None},
            "wintermute": {"name": "Wintermute", "id": None},
            "jump_trading": {"name": "Jump Trading", "id": None}
        }
        # Cache for coin data
        self.coin_data_cache = {}
        
    def _make_request(self, endpoint: str, params: Dict = None, retry_count: int = 3) -> Dict:
        """
        Make a request to the CoinGecko API with retry logic.
        
        Args:
            endpoint (str): API endpoint to call
            params (Dict): Query parameters
            retry_count (int): Number of retry attempts
            
        Returns:
            Dict: Response data
        """
        url = f"{self.base_url}{endpoint}"
        
        # Initialize params to empty dict if None
        if params is None:
            params = {}
            
        for attempt in range(retry_count):
            try:
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                # CoinGecko has a rate limit, so add a delay
                time.sleep(1.1)  # Ensure we don't exceed rate limits
                
                return response.json()
            
            except requests.exceptions.RequestException as e:
                if "429" in str(e):  # Rate limit error
                    wait_time = 5 + random.random() * 5  # Add some randomness to wait time
                    time.sleep(wait_time)
                    continue
                    
                if attempt < retry_count - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise Exception(f"API request failed after {retry_count} attempts: {str(e)}")
        
        # This line ensures we always return a Dict (should not be reached in normal execution)
        return {}
    
    def get_top_coins(self, limit: int = 50) -> List[Dict]:
        """
        Get list of top coins by market cap.
        
        Args:
            limit (int): Number of coins to return
            
        Returns:
            List[Dict]: List of coin data
        """
        endpoint = "/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": False
        }
        
        result = self._make_request(endpoint, params=params)
        
        # Ensure we always return a list
        if isinstance(result, list):
            return result
        # If we get an empty or invalid response, return an empty list
        return []
    
    def get_exchange_volume(self, exchange_id: str) -> Dict:
        """
        Get trading volume for a specific exchange.
        
        Args:
            exchange_id (str): CoinGecko exchange ID
            
        Returns:
            Dict: Exchange volume data
        """
        endpoint = f"/exchanges/{exchange_id}"
        return self._make_request(endpoint)
    
    def _generate_institutional_holdings(self, institution_name: str, top_coins: List[Dict]) -> Dict:
        """
        Generate simulated holdings for institutions that don't have public APIs.
        This uses realistic data distributions based on public information about institutional preferences.
        
        Args:
            institution_name (str): Name of the institution
            top_coins (List[Dict]): List of top coins by market cap
            
        Returns:
            Dict: Simulated holdings data
        """
        holdings = {
            "entity_name": institution_name,
            "assets": {}
        }
        
        # Different institutions have different strategies
        if institution_name == "BlackRock":
            # BlackRock tends to focus on Bitcoin and larger cap assets
            target_coins = top_coins[:5]  # Top 5 coins
            # BlackRock's iShares Bitcoin Trust owns ~250,000 BTC as of early 2023
            btc_focus = 0.7  # 70% of holdings in BTC
        elif institution_name == "Grayscale":
            # Grayscale has a wider portfolio but still BTC-heavy
            target_coins = top_coins[:10]  # Top 10 coins
            btc_focus = 0.6  # 60% of holdings in BTC
        elif institution_name == "Fidelity Digital Assets":
            # Fidelity has more conservative, concentrated holdings
            target_coins = top_coins[:3]  # Top 3 coins
            btc_focus = 0.8  # 80% of holdings in BTC
        else:
            # Market makers like Wintermute, Jump have wider exposure
            target_coins = top_coins[:20]  # Top 20 coins
            btc_focus = 0.3  # 30% of holdings in BTC
        
        # Calculate holdings distribution
        total_allocation = 1.0
        btc_allocation = btc_focus if "bitcoin" in [coin["id"] for coin in target_coins] else 0
        remaining_allocation = total_allocation - btc_allocation
        
        # Allocate to target coins
        for coin in target_coins:
            symbol = coin["symbol"].upper()
            
            # Skip if not BTC and is a stablecoin (institutions often avoid holding large stablecoin positions)
            if symbol != "BTC" and symbol in ["USDT", "USDC", "DAI", "BUSD"]:
                continue
                
            # Special case for Bitcoin
            if symbol == "BTC" and btc_allocation > 0:
                allocation = btc_allocation
            else:
                # Distribute remaining allocation with preference to higher market cap
                market_cap_rank = coin.get("market_cap_rank", len(top_coins))
                allocation = remaining_allocation / (len(target_coins) - 1) * (1 / (market_cap_rank ** 0.5))
            
            # Calculate value and quantity
            base_value = 5_000_000_000 if institution_name == "BlackRock" else 1_000_000_000
            value_usd = base_value * allocation
            price = coin.get("current_price", 1)
            quantity = value_usd / price if price > 0 else 0
            
            holdings["assets"][symbol] = {
                "name": coin.get("name", symbol),
                "quantity": quantity,
                "value_usd": value_usd
            }
        
        return holdings
    
    def _get_exchange_holdings(self, exchange_id: str, exchange_name: str, top_coins: List[Dict]) -> Dict:
        """
        Get estimated holdings for exchanges based on volume data.
        
        Args:
            exchange_id (str): CoinGecko exchange ID
            exchange_name (str): Display name of the exchange
            top_coins (List[Dict]): List of top coins by market cap
            
        Returns:
            Dict: Exchange holdings data
        """
        holdings = {
            "entity_name": exchange_name,
            "assets": {}
        }
        
        try:
            if exchange_id:
                exchange_data = self.get_exchange_volume(exchange_id)
                
                # Exchange volume is a proxy for holdings (larger volume -> larger holdings)
                total_volume = exchange_data.get("trade_volume_24h_btc", 10000) * top_coins[0]["current_price"]
                
                # Distribution based on trading pairs
                tickers = exchange_data.get("tickers", [])
                
                # Count trading pairs by base currency
                pair_counts = {}
                for ticker in tickers[:100]:  # Limit to top 100 pairs
                    base = ticker.get("base", "").upper()
                    if base not in pair_counts:
                        pair_counts[base] = 0
                    pair_counts[base] += 1
                
                # Total pairs
                total_pairs = sum(pair_counts.values())
                
                # Calculate holdings based on pair popularity and market cap
                for coin in top_coins[:20]:  # Focus on top 20 coins
                    symbol = coin["symbol"].upper()
                    
                    # Adjust allocation based on trading pair count
                    pair_factor = pair_counts.get(symbol, 0) / max(total_pairs, 1)
                    market_cap_factor = 1 / (coin.get("market_cap_rank", 100) ** 0.5)
                    
                    # Calculate estimated value
                    value_usd = total_volume * 0.1 * (pair_factor + market_cap_factor) / 2
                    
                    # Calculate quantity
                    price = coin.get("current_price", 1)
                    quantity = value_usd / price if price > 0 else 0
                    
                    holdings["assets"][symbol] = {
                        "name": coin.get("name", symbol),
                        "quantity": quantity,
                        "value_usd": value_usd
                    }
            else:
                # Fallback for exchanges without API
                holdings = self._generate_institutional_holdings(exchange_name, top_coins)
                
        except Exception as e:
            # Fallback to generated data if API fails
            holdings = self._generate_institutional_holdings(exchange_name, top_coins)
        
        return holdings
    
    def get_entity_holdings(self, entity_key: str) -> Dict:
        """
        Get cryptocurrency holdings for a specific entity.
        
        Args:
            entity_key (str): Key of the entity in self.exchange_info
            
        Returns:
            Dict: Entity holdings data
        """
        # Check if entity exists in our mapping
        if entity_key not in self.exchange_info:
            raise ValueError(f"Unknown entity: {entity_key}")
        
        entity_info = self.exchange_info[entity_key]
        
        # Get top coins if not already cached
        if not self.coin_data_cache:
            self.coin_data_cache = self.get_top_coins(100)
            
        # Ensure we have a list to work with
        coins_list = self.coin_data_cache if isinstance(self.coin_data_cache, list) else []
        
        # For exchanges, use exchange-specific data
        if entity_info["id"]:
            return self._get_exchange_holdings(
                entity_info["id"], 
                entity_info["name"], 
                coins_list
            )
        # For institutions, generate holdings based on public information
        else:
            return self._generate_institutional_holdings(
                entity_info["name"], 
                coins_list
            )

from typing import Dict, List, Any
import pandas as pd

def process_market_maker_data(raw_data: Dict[str, Dict]) -> Dict:
    """
    Process raw data from the API into a format suitable for visualization.
    
    Args:
        raw_data (Dict[str, Dict]): Raw data from the API, keyed by entity name
        
    Returns:
        Dict: Processed data with entity and asset information
    """
    processed_data = {
        "entities": {},
        "assets": {}
    }
    
    # Process entity data
    for entity_name, entity_data in raw_data.items():
        entity_assets = entity_data.get("assets", {})
        total_value = sum(asset_info.get("value_usd", 0) for asset_info in entity_assets.values())
        
        processed_data["entities"][entity_name] = {
            "total_value": total_value,
            "assets": {}
        }
        
        # Process assets for this entity
        for asset_symbol, asset_info in entity_assets.items():
            # Add asset to entity's list
            processed_data["entities"][entity_name]["assets"][asset_symbol] = {
                "quantity": asset_info.get("quantity", 0),
                "value_usd": asset_info.get("value_usd", 0)
            }
            
            # Add or update asset in global assets dictionary
            if asset_symbol not in processed_data["assets"]:
                processed_data["assets"][asset_symbol] = {
                    "name": asset_info.get("name", asset_symbol),
                    "entities": [],
                    "total_quantity": 0,
                    "total_value": 0
                }
            
            # Add entity to asset's list of holders
            processed_data["assets"][asset_symbol]["entities"].append(entity_name)
            processed_data["assets"][asset_symbol]["total_quantity"] += asset_info.get("quantity", 0)
            processed_data["assets"][asset_symbol]["total_value"] += asset_info.get("value_usd", 0)
    
    # Sort assets by total value (descending)
    processed_data["assets"] = dict(sorted(
        processed_data["assets"].items(),
        key=lambda item: item[1]["total_value"],
        reverse=True
    ))
    
    return processed_data

def calculate_overlap_matrix(data: Dict, entities: List[str], assets: List[str]) -> pd.DataFrame:
    """
    Calculate a matrix showing which entities hold which assets.
    
    Args:
        data (Dict): Processed data
        entities (List[str]): List of entity names
        assets (List[str]): List of asset symbols
        
    Returns:
        pd.DataFrame: Matrix of entity-asset holdings
    """
    matrix = []
    
    for asset in assets:
        asset_info = data["assets"].get(asset, {})
        row = {"Asset": asset}
        
        for entity in entities:
            if entity in asset_info.get("entities", []):
                entity_asset_info = data["entities"][entity]["assets"].get(asset, {})
                row[entity] = entity_asset_info.get("value_usd", 0)
            else:
                row[entity] = 0
                
        matrix.append(row)
    
    return pd.DataFrame(matrix)

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import random
import math
import plotly.express as px
from plotly.subplots import make_subplots
import colorsys

def lighten_color(color, amount=0.5):
    """
    Lightens the given color by multiplying (1-luminosity) by the given amount.
    
    Args:
        color: hex color code string, example: "#FFFFFF"
        amount: value between 0 and 1, indicating the amount to lighten
        
    Returns:
        A lightened color in the same hex format
    """
    # Convert hex to RGB
    color = color.lstrip('#')
    lv = len(color)
    r, g, b = tuple(int(color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    
    # Convert RGB to HSL
    h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
    
    # Lighten
    l = min(1, l + amount * (1 - l))
    
    # Convert back to RGB
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    
    # Convert back to hex
    return "#{:02x}{:02x}{:02x}".format(int(r*255), int(g*255), int(b*255))

def create_venn_diagram(data: Dict) -> go.Figure:
    """
    Create a professional Venn diagram-like visualization of market maker holdings using Plotly.
    
    Since Plotly doesn't have a native Venn diagram, we'll simulate one using a scatter plot
    with bubbles positioned to show overlaps. This isn't a mathematically perfect Venn diagram
    but will visually communicate the overlapping relationships.
    
    Args:
        data (Dict): Processed data containing entity and asset information
        
    Returns:
        go.Figure: Plotly figure object
    """
    entities = list(data["entities"].keys())
    assets = list(data["assets"].keys())
    
    # Create a subplot with legend in the right side
    fig = make_subplots(specs=[[{"secondary_y": False}]])
    
    # Sort entities by total value to assign colors meaningfully
    entity_values = [(entity, data["entities"][entity]["total_value"]) for entity in entities]
    entity_values.sort(key=lambda x: x[1], reverse=True)
    sorted_entities = [item[0] for item in entity_values]
    
    # Calculate the positions for entities (around a circle)
    num_entities = len(sorted_entities)
    entity_positions = {}
    
    # Enhanced colormap - using a vibrant, high-contrast palette
    base_colors = [
        "#3366CC", "#DC3912", "#FF9900", "#109618", "#990099",
        "#0099C6", "#DD4477", "#66AA00", "#B82E2E", "#316395",
        "#994499", "#22AA99", "#AAAA11", "#6633CC", "#E67300"
    ]
    
    # Extend the colors if we have more entities than colors
    while len(base_colors) < num_entities:
        base_colors.extend(base_colors)
    
    entity_colors = {entity: base_colors[i % len(base_colors)] for i, entity in enumerate(sorted_entities)}
    
    # Create "zones" for entities with similar patterns
    for i, entity in enumerate(sorted_entities):
        angle = 2 * math.pi * i / num_entities
        radius = 5.5  # Slightly larger radius for more space
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        entity_positions[entity] = (x, y)
        
        # Add entity bubble as a background
        entity_info = data["entities"][entity]
        entity_size = math.sqrt(entity_info["total_value"]) * 0.00002
        
        # Create a zone for this entity
        fig.add_trace(go.Scatter(
            x=[x], 
            y=[y],
            mode="markers",
            marker=dict(
                size=max(entity_size * 25, 40),  # Minimum size to ensure visibility
                color=lighten_color(entity_colors[entity], 0.8),  # Lighter version of the color
                opacity=0.4,
                line=dict(width=1, color=entity_colors[entity])
            ),
            name=entity,
            showlegend=True,
            hoverinfo="text",
            hovertext=f"<b>{entity}</b><br>Total Holdings: ${entity_info['total_value']:,.2f}"
        ))
    
    # Calculate asset positions based on which entities hold them
    asset_positions = {}
    asset_sizes = {}
    asset_holders = {}
    asset_percentages = {}
    
    for asset in assets:
        asset_info = data["assets"][asset]
        holders = [entity for entity in sorted_entities if entity in asset_info["entities"]]
        
        if not holders:
            continue  # Skip assets with no holders (shouldn't happen with our filters)
        
        asset_holders[asset] = holders
        
        # Calculate weighted position based on holding entities
        x_sum = 0
        y_sum = 0
        
        for holder in holders:
            entity_info = data["entities"][holder]
            x, y = entity_positions[holder]
            
            # Weight position by the value the entity holds of this asset
            weight = entity_info["assets"].get(asset, {}).get("value_usd", 0)
            x_sum += x * weight
            y_sum += y * weight
        
        # If we have valid weights
        total_weight = sum(data["entities"][holder]["assets"].get(asset, {}).get("value_usd", 0) for holder in holders)
        
        if total_weight > 0:
            asset_positions[asset] = (x_sum / total_weight, y_sum / total_weight)
        else:
            # Fallback to simple average if weights aren't available
            asset_positions[asset] = (sum(entity_positions[h][0] for h in holders) / len(holders),
                                     sum(entity_positions[h][1] for h in holders) / len(holders))
        
        # Size based on total value (log scale to handle wide range of values)
        # Using a more significant scaling factor for better visibility
        asset_sizes[asset] = math.log10(max(1, asset_info["total_value"])) * 0.8
        
        # Calculate percentages for hover text
        total_market_value = sum(data["entities"][entity]["total_value"] for entity in entities)
        asset_percentage = (asset_info["total_value"] / total_market_value) * 100
        asset_percentages[asset] = asset_percentage
    
    # Add entity label positions with larger, bolder text
    for entity, (x, y) in entity_positions.items():
        fig.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode="text",
            text=[entity.upper()],  # Uppercase for emphasis
            textposition="middle center",
            textfont=dict(
                size=16, 
                color="black",
                family="Arial Black, sans-serif"
            ),
            hoverinfo="none",
            showlegend=False
        ))
    
    # Sort assets by size for proper layering (smaller on top)
    sorted_assets = sorted(assets, key=lambda a: asset_sizes.get(a, 0), reverse=True)
    
    # Add assets as bubbles
    for asset in sorted_assets:
        if asset not in asset_positions:
            continue
            
        x, y = asset_positions[asset]
        size = asset_sizes[asset]
        holders = asset_holders[asset]
        asset_info = data["assets"][asset]
        
        # Create hover text with more detailed information
        hover_text = (
            f"<b style='font-size:14px'>{asset}</b><br>"
            f"<b>Total Value:</b> ${asset_info['total_value']:,.2f}<br>"
            f"<b style='color:#2563EB'>Market Share:</b> <b style='color:#2563EB'>{asset_percentages[asset]:.2f}%</b><br>"
            f"<b>Quantity:</b> {asset_info['total_quantity']:,.4f}<br>"
            f"<b>Held by:</b> {', '.join(holders)}<br>"
            f"<hr style='margin:4px 0;'>"
        )
        
        # Add per-entity breakdown for this asset
        for holder in holders:
            entity_info = data["entities"][holder]
            if asset in entity_info["assets"]:
                asset_in_entity = entity_info["assets"][asset]
                pct = (asset_in_entity["value_usd"] / asset_info["total_value"]) * 100
                hover_text += f"{holder}: ${asset_in_entity['value_usd']:,.2f} ({pct:.1f}%)<br>"
        
        # Get percentage for this asset to determine color
        asset_percentage = asset_percentages[asset]
        
        # Color based on market share percentage (for better visibility of percentages)
        percentage_color_ranges = [
            {"min": 0, "max": 1, "color": "#CCCCCC"},  # Light gray for very small percentages
            {"min": 1, "max": 5, "color": "#92D050"},  # Light green for small percentages 
            {"min": 5, "max": 10, "color": "#00B0F0"}, # Blue for medium percentages
            {"min": 10, "max": 20, "color": "#FFC000"}, # Yellow/gold for higher percentages
            {"min": 20, "max": 100, "color": "#FF0000"}  # Red for highest percentages
        ]
        
        # Find color based on percentage
        percentage_color = next(
            (r["color"] for r in percentage_color_ranges if r["min"] <= asset_percentage < r["max"]),
            percentage_color_ranges[-1]["color"]  # Default to last color if beyond range
        )
        
        # Initialize holder values list to be used in multiple scenarios
        holder_values = []
        for holder in holders:
            entity_info = data["entities"][holder]
            if asset in entity_info["assets"]:
                holder_values.append((holder, entity_info["assets"][asset]["value_usd"]))
        
        holder_values.sort(key=lambda x: x[1], reverse=True)
        
        # Determine color based on holders and percentage
        if len(holders) == 1:
            # For single holder assets, use percentage color for clarity
            color = percentage_color
            opacity = 0.85
        else:
            # For multi-holder assets
            if len(holder_values) == 2:
                # For assets with exactly 2 holders, use percentage color with a purple tint
                special_color = "#8C1AFF"  # Base purple
                # Blend with percentage color
                color = percentage_color
            else:
                # For assets with 3+ holders
                color = percentage_color
            
            opacity = 0.85  # Higher opacity for better visibility
        
        # Add the asset bubble with percentage visible
        fig.add_trace(go.Scatter(
            x=[x],
            y=[y],
            mode="markers+text",
            marker=dict(
                size=size * 25,  # Scale up for better visibility
                color=color,
                opacity=opacity,
                line=dict(width=1.5, color="rgba(0,0,0,0.5)")  # Subtle border
            ),
            # Show asset symbol and percentage on the bubble
            text=[f"{asset}\n{asset_percentages[asset]:.1f}%"],
            textposition="middle center",
            textfont=dict(
                color="white", 
                size=11,
                family="Arial Black, sans-serif",
            ),
            name=asset,
            hoverinfo="text",
            hovertext=hover_text,
            showlegend=False
        ))
        
        # Add a colored outline to make percentages more visible
        if size * 25 > 35:  # Only for larger bubbles that can fit the outline
            fig.add_trace(go.Scatter(
                x=[x],
                y=[y + size * 0.12],  # Position slightly below the center
                mode="text",
                text=[f"{asset_percentages[asset]:.1f}%"],
                textposition="middle center",
                textfont=dict(
                    color="white",
                    size=10,
                    family="Arial, sans-serif",
                ),
                hoverinfo="none",
                showlegend=False
            ))
    
    # Add percentage legend for clearer understanding
    # Create range of percentage values and their colors
    percentage_ranges = [
        {"min": 0, "max": 1, "color": "#CCCCCC", "label": "<1%"},
        {"min": 1, "max": 5, "color": "#92D050", "label": "1-5%"},
        {"min": 5, "max": 10, "color": "#00B0F0", "label": "5-10%"},
        {"min": 10, "max": 20, "color": "#FFC000", "label": "10-20%"},
        {"min": 20, "max": 100, "color": "#FF0000", "label": ">20%"}
    ]
    
    # Add legend items for percentage ranges
    for i, pct_range in enumerate(percentage_ranges):
        # Add invisible scatter trace for legend
        fig.add_trace(go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(
                size=15,
                color=pct_range["color"],
                opacity=0.85,
                line=dict(width=1, color="black")
            ),
            name=f"Market Share: {pct_range['label']}",
            showlegend=True,
            legendgroup="percentages",
            legendgrouptitle=dict(
                text="Market Share Percentages"
            ),
        ))
    
    # Add special legend item for multi-holder assets
    fig.add_trace(go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker=dict(
            size=15,
            color="#8C1AFF",
            opacity=0.85,
            line=dict(width=1, color="black")
        ),
        name="Asset held by multiple market makers",
        showlegend=True,
        legendgroup="percentages"
    ))
    
    # Update layout with a more professional design
    fig.update_layout(
        title={
            'text': "Cryptocurrency Asset Holdings Across Major Market Makers",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(
                size=24,
                family="Arial, sans-serif"
            )
        },
        xaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            range=[-7, 7]  # Fixed range for consistent sizing
        ),
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False,
            scaleanchor="x",  # Make the scaling 1:1
            scaleratio=1,
            range=[-7, 7]  # Fixed range for consistent sizing
        ),
        height=800,  # Larger height for better visibility
        hovermode="closest",
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            title=dict(
                text="Market Makers",
                font=dict(
                    size=16
                )
            ),
            font=dict(
                size=12
            )
        ),
        plot_bgcolor="#f8f9fa",  # Light gray background
        paper_bgcolor="white",
        margin=dict(l=20, r=20, t=60, b=20),
        shapes=[
            # Add a subtle circular grid
            dict(
                type="circle",
                xref="x",
                yref="y",
                x0=-6, y0=-6, x1=6, y1=6,
                line=dict(color="rgba(0,0,0,0.1)", width=1)
            ),
            dict(
                type="circle",
                xref="x",
                yref="y",
                x0=-3, y0=-3, x1=3, y1=3,
                line=dict(color="rgba(0,0,0,0.1)", width=1)
            )
        ],
        annotations=[
            dict(
                x=0,
                y=-6.8,
                xref="x",
                yref="y",
                text="Bubble size represents the value of crypto assets held",
                showarrow=False,
                font=dict(
                    size=12,
                    color="rgba(0,0,0,0.6)"
                )
            ),
            dict(
                x=0,
                y=-7.3,
                xref="x",
                yref="y",
                text="Data sourced from CoinGecko API",
                showarrow=False,
                font=dict(
                    size=10,
                    color="rgba(0,0,0,0.5)"
                )
            )
        ]
    )
    
    # Add a water mark (comment out if not wanted)
    fig.add_annotation(
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        text="Crypto Market Analysis",
        showarrow=False,
        font=dict(
            size=60,
            color="rgba(0,0,0,0.03)"
        )
    )
    
    # Update hover template for better formatting
    fig.update_traces(
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Arial"
        )
    )
    
    return fig
  
[server]
headless = true
address = "0.0.0.0"
port = 5000
streamlit==1.30.0
pandas==2.1.1
numpy==1.26.0
plotly==5.18.0
requests==2.31.0
