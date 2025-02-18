import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS


def test_initial_custom_oracle_state(oracle_custom, charlie_token):
    # Test initial state
    assert oracle_custom.hasPriceFeed(charlie_token) == False
    assert oracle_custom.getPrice(charlie_token) == 0
    price, has_feed = oracle_custom.getPriceAndHasFeed(charlie_token)
    assert price == 0
    assert has_feed == False
    assert oracle_custom.numAssets() == 0
    assert len(oracle_custom.getConfiguredAssets()) == 0


def test_set_price(oracle_custom, charlie_token, governor):
    # Test setting price
    price = 1000 * 10**18
    oracle_custom.setPrice(charlie_token, price, sender=governor)
    
    # Verify price is set correctly
    assert oracle_custom.hasPriceFeed(charlie_token) == True
    assert oracle_custom.getPrice(charlie_token) == price
    stored_price, has_feed = oracle_custom.getPriceAndHasFeed(charlie_token)
    assert stored_price == price
    assert has_feed == True
    
    # Verify asset is tracked in OracleAssetData
    assert oracle_custom.numAssets() == 2  # starts from 1
    assets = oracle_custom.getConfiguredAssets()
    assert len(assets) == 1
    assert assets[0] == charlie_token.address


def test_disable_price_feed(oracle_custom, charlie_token, governor):
    # First set a price
    price = 1000 * 10**18
    oracle_custom.setPrice(charlie_token, price, sender=governor)
    assert oracle_custom.hasPriceFeed(charlie_token) == True
    
    # Test disabling price feed
    assert oracle_custom.disablePriceFeed(charlie_token, sender=governor) == True
    
    # Verify price feed is disabled
    assert oracle_custom.hasPriceFeed(charlie_token) == False
    assert oracle_custom.getPrice(charlie_token) == 0
    price, has_feed = oracle_custom.getPriceAndHasFeed(charlie_token)
    assert price == 0
    assert has_feed == False
    
    # Verify asset is removed from tracking
    assert oracle_custom.numAssets() == 1  # back to initial state
    assert len(oracle_custom.getConfiguredAssets()) == 0


def test_stale_price(oracle_custom, charlie_token, governor):
    price = 1000 * 10**18
    oracle_custom.setPrice(charlie_token, price, sender=governor)
    
    # Test with no stale time (should return price)
    assert oracle_custom.getPrice(charlie_token) == price
    
    # Test with future stale time (should return price)
    assert oracle_custom.getPrice(charlie_token, 3600) == price
    
    # Advance time beyond stale threshold
    boa.env.time_travel(3601)
    
    # Test with past stale time (should return 0)
    assert oracle_custom.getPrice(charlie_token, 3600) == 0
    # But hasPriceFeed should still return True
    assert oracle_custom.hasPriceFeed(charlie_token) == True


def test_multiple_assets(oracle_custom, alpha_token, bravo_token, charlie_token, governor):
    tokens = [
        alpha_token.address,
        bravo_token.address,
        charlie_token.address
    ]
    prices = [1000 * 10**18, 2000 * 10**18, 3000 * 10**18]
    
    # Set prices for multiple tokens
    for token, price in zip(tokens, prices):
        oracle_custom.setPrice(token, price, sender=governor)
    
    # Verify all prices are set correctly
    for token, price in zip(tokens, prices):
        assert oracle_custom.getPrice(token) == price
        assert oracle_custom.hasPriceFeed(token) == True
    
    # Verify asset tracking
    assert oracle_custom.numAssets() == 4  # starts from 1
    assets = oracle_custom.getConfiguredAssets()
    assert len(assets) == 3
    for token in tokens:
        assert token in assets


def test_multiple_assets_and_remove(oracle_custom, alpha_token, bravo_token, charlie_token, governor):
    tokens = [
        alpha_token.address,
        bravo_token.address,
        charlie_token.address
    ]
    prices = [1000 * 10**18, 2000 * 10**18, 3000 * 10**18]
    
    # Set prices for multiple tokens
    for token, price in zip(tokens, prices):
        oracle_custom.setPrice(token, price, sender=governor)
    
    # Verify asset tracking
    assert oracle_custom.numAssets() == 4  # starts from 1
    assets = oracle_custom.getConfiguredAssets()
    assert len(assets) == 3
    for token in tokens:
        assert token in assets

    assert oracle_custom.disablePriceFeed(bravo_token, sender=governor) == True
    assert oracle_custom.numAssets() == 3
    assets = oracle_custom.getConfiguredAssets()
    assert len(assets) == 2
    assert assets[0] == alpha_token.address
    assert assets[1] == charlie_token.address

    assert oracle_custom.disablePriceFeed(alpha_token, sender=governor) == True
    assert oracle_custom.numAssets() == 2
    assets = oracle_custom.getConfiguredAssets()
    assert len(assets) == 1

    assert assets[0] == charlie_token.address


def test_permissions(oracle_custom, charlie_token, bob):
    with boa.reverts("no perms"):
        oracle_custom.setPrice(charlie_token, 1000 * 10**18, sender=bob)
        
    # Try to disable price feed as non-governor
    with boa.reverts("no perms"):
        oracle_custom.disablePriceFeed(charlie_token, sender=bob)