import pytest
import boa

from constants import ZERO_ADDRESS, YIELD_OPP_UINT256
from conf_utils import filter_logs


@pytest.fixture(scope="module")
def new_mock_lego(lego_registry, addy_registry_deploy, governor):
    addr = boa.load("contracts/mock/MockLego.vy", addy_registry_deploy, name="lego_morpho")
    lego_registry.registerNewLego(addr, "New Mock Lego", YIELD_OPP_UINT256, sender=governor)
    boa.env.time_travel(blocks=lego_registry.legoChangeDelay() + 1)
    assert lego_registry.confirmNewLegoRegistration(addr, sender=governor) != 0
    return addr


#########
# Tests #
#########


def test_add_asset_opportunity(new_mock_lego, governor, alpha_token, alpha_token_erc4626_vault, bob):
    # Test adding first asset opportunity
    assert new_mock_lego.numAssetOpportunities(alpha_token) == 0
    assert new_mock_lego.numAssets() == 0

    # Test that non-governor cannot add asset opportunity
    with boa.reverts("no perms"):
        new_mock_lego.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=bob)

    # Add asset opportunity
    assert new_mock_lego.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)

    log = filter_logs(new_mock_lego, "AssetOpportunityAdded")[0]
    assert log.asset == alpha_token.address
    assert log.vaultToken == alpha_token_erc4626_vault.address

    # Verify asset opportunity was added
    assert new_mock_lego.numAssetOpportunities(alpha_token) == 2  # Index starts at 1
    assert new_mock_lego.assetOpportunities(alpha_token, 1) == alpha_token_erc4626_vault.address
    assert new_mock_lego.indexOfAssetOpportunity(alpha_token, alpha_token_erc4626_vault) == 1
    
    # Verify asset was added
    assert new_mock_lego.numAssets() == 2  # Index starts at 1
    assert new_mock_lego.assets(1) == alpha_token.address
    assert new_mock_lego.indexOfAsset(alpha_token) == 1

    # Try to add same opportunity again
    with boa.reverts("asset + vault token already added"):
        new_mock_lego.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)


def test_remove_asset_opportunity(new_mock_lego, governor, alpha_token, alpha_token_erc4626_vault, bob):
    # Try to remove an asset opportunity that doesn't exist
    with boa.reverts("asset + vault token not found"):
        new_mock_lego.removeAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)

    # First add an asset opportunity
    assert new_mock_lego.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)

    # Test that non-governor cannot remove asset opportunity
    with boa.reverts("no perms"):
        new_mock_lego.removeAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=bob)

    # Remove the asset opportunity
    assert new_mock_lego.removeAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)

    log = filter_logs(new_mock_lego, "AssetOpportunityRemoved")[0]
    assert log.asset == alpha_token.address
    assert log.vaultToken == alpha_token_erc4626_vault.address
    
    # Verify asset opportunity was removed
    assert new_mock_lego.numAssetOpportunities(alpha_token) == 1  # Back to 1 since we removed it
    assert new_mock_lego.indexOfAssetOpportunity(alpha_token, alpha_token_erc4626_vault) == 0
    
    # Verify asset was removed since it was the last opportunity
    assert new_mock_lego.numAssets() == 1  # Back to 1 since we removed it
    assert new_mock_lego.indexOfAsset(alpha_token) == 0


def test_multiple_asset_opportunities(new_mock_lego, governor, alpha_token, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another):
    # Add first opportunity
    assert new_mock_lego.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)
    
    # Add second vault for same asset
    assert new_mock_lego.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault_another, sender=governor)

    # Verify asset was added
    assert new_mock_lego.numAssets() == 2  # Index starts at 1
    assert new_mock_lego.assets(1) == alpha_token.address
    assert new_mock_lego.indexOfAsset(alpha_token) == 1

    # Verify both opportunities exist
    assert new_mock_lego.numAssetOpportunities(alpha_token) == 3  # Index starts at 1
    assert new_mock_lego.assetOpportunities(alpha_token, 1) == alpha_token_erc4626_vault.address
    assert new_mock_lego.assetOpportunities(alpha_token, 2) == alpha_token_erc4626_vault_another.address
    
    # Remove first opportunity
    assert new_mock_lego.removeAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)
    assert new_mock_lego.indexOfAssetOpportunity(alpha_token, alpha_token_erc4626_vault) == 0
    
    # Verify second opportunity still exists and was shifted
    assert new_mock_lego.numAssetOpportunities(alpha_token) == 2
    assert new_mock_lego.assetOpportunities(alpha_token, 1) == alpha_token_erc4626_vault_another.address
    assert new_mock_lego.indexOfAssetOpportunity(alpha_token, alpha_token_erc4626_vault_another) == 1


def test_edge_cases_asset_opportunities(new_mock_lego, governor, alpha_token, alpha_token_erc4626_vault):
    # Test accessing non-existent indices
    assert new_mock_lego.assetOpportunities(alpha_token, 0) == ZERO_ADDRESS
    assert new_mock_lego.assetOpportunities(alpha_token, 999) == ZERO_ADDRESS
    
    # Test with empty addresses
    with boa.reverts():
        new_mock_lego.addAssetOpportunity(ZERO_ADDRESS, alpha_token_erc4626_vault, sender=governor)
    
    with boa.reverts():
        new_mock_lego.addAssetOpportunity(alpha_token, ZERO_ADDRESS, sender=governor)

    # Add and remove to test last opportunity behavior
    assert new_mock_lego.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)
    assert new_mock_lego.removeAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)
    
    # Verify state is clean after removing last opportunity
    assert new_mock_lego.numAssetOpportunities(alpha_token) == 1  # Back to 1
    assert new_mock_lego.numAssets() == 1  # Back to 1
    assert new_mock_lego.indexOfAsset(alpha_token) == 0
    assert new_mock_lego.indexOfAssetOpportunity(alpha_token, alpha_token_erc4626_vault) == 0


def test_complex_index_management(new_mock_lego, governor, alpha_token, bravo_token, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, bravo_token_erc4626_vault):
    # Add multiple opportunities for different assets
    assert new_mock_lego.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)
    assert new_mock_lego.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault_another, sender=governor)
    assert new_mock_lego.addAssetOpportunity(bravo_token, bravo_token_erc4626_vault, sender=governor)
    
    # Verify initial state
    assert new_mock_lego.numAssets() == 3  # Index starts at 1
    assert new_mock_lego.assets(1) == alpha_token.address
    assert new_mock_lego.assets(2) == bravo_token.address
    
    # Remove first asset's first opportunity
    assert new_mock_lego.removeAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)
    
    # Verify indices were properly shifted
    assert new_mock_lego.numAssetOpportunities(alpha_token) == 2
    assert new_mock_lego.assetOpportunities(alpha_token, 1) == alpha_token_erc4626_vault_another.address
    
    # Remove last opportunity for first asset
    assert new_mock_lego.removeAssetOpportunity(alpha_token, alpha_token_erc4626_vault_another, sender=governor)
    
    # Verify bravo_token was shifted to first position in assets
    assert new_mock_lego.numAssets() == 2
    assert new_mock_lego.assets(1) == bravo_token.address
    assert new_mock_lego.indexOfAsset(bravo_token) == 1
    assert new_mock_lego.indexOfAsset(alpha_token) == 0


def test_asset_removal_order_independence(new_mock_lego, governor, alpha_token, bravo_token, charlie_token, 
                                        alpha_token_erc4626_vault, bravo_token_erc4626_vault, charlie_token_erc4626_vault):
    # Add opportunities in order: alpha, beta, charlie
    assert new_mock_lego.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)
    assert new_mock_lego.addAssetOpportunity(bravo_token, bravo_token_erc4626_vault, sender=governor)
    assert new_mock_lego.addAssetOpportunity(charlie_token, charlie_token_erc4626_vault, sender=governor)
    
    # Remove in different order: beta, alpha, charlie
    assert new_mock_lego.removeAssetOpportunity(bravo_token, bravo_token_erc4626_vault, sender=governor)
    assert new_mock_lego.numAssets() == 3
    assert new_mock_lego.assets(2) == charlie_token.address  # charlie should have shifted to beta's position
    
    assert new_mock_lego.removeAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)
    assert new_mock_lego.numAssets() == 2
    assert new_mock_lego.assets(1) == charlie_token.address  # charlie should now be first
    
    assert new_mock_lego.removeAssetOpportunity(charlie_token, charlie_token_erc4626_vault, sender=governor)
    assert new_mock_lego.numAssets() == 1  # Back to initial state


def test_get_asset_opportunities(new_mock_lego, governor, alpha_token, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another):
    # Test empty state
    assert len(new_mock_lego.getAssetOpportunities(alpha_token)) == 0

    # Add first opportunity
    assert new_mock_lego.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)
    opportunities = new_mock_lego.getAssetOpportunities(alpha_token)
    assert len(opportunities) == 1
    assert opportunities[0] == alpha_token_erc4626_vault.address

    # Add second opportunity
    assert new_mock_lego.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault_another, sender=governor)
    opportunities = new_mock_lego.getAssetOpportunities(alpha_token)
    assert len(opportunities) == 2
    assert opportunities[0] == alpha_token_erc4626_vault.address
    assert opportunities[1] == alpha_token_erc4626_vault_another.address

    # Remove first opportunity and verify list is updated
    assert new_mock_lego.removeAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)
    opportunities = new_mock_lego.getAssetOpportunities(alpha_token)
    assert len(opportunities) == 1
    assert opportunities[0] == alpha_token_erc4626_vault_another.address

    # Remove last opportunity
    assert new_mock_lego.removeAssetOpportunity(alpha_token, alpha_token_erc4626_vault_another, sender=governor)
    assert len(new_mock_lego.getAssetOpportunities(alpha_token)) == 0


def test_get_assets(new_mock_lego, governor, alpha_token, bravo_token, charlie_token, 
                    alpha_token_erc4626_vault, bravo_token_erc4626_vault, charlie_token_erc4626_vault):
    # Test empty state
    assert len(new_mock_lego.getAssets()) == 0

    # Add first asset opportunity
    assert new_mock_lego.addAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)
    assets = new_mock_lego.getAssets()
    assert len(assets) == 1
    assert assets[0] == alpha_token.address

    # Add second asset opportunity
    assert new_mock_lego.addAssetOpportunity(bravo_token, bravo_token_erc4626_vault, sender=governor)
    assets = new_mock_lego.getAssets()
    assert len(assets) == 2
    assert assets[0] == alpha_token.address
    assert assets[1] == bravo_token.address

    # Add third asset opportunity
    assert new_mock_lego.addAssetOpportunity(charlie_token, charlie_token_erc4626_vault, sender=governor)
    assets = new_mock_lego.getAssets()
    assert len(assets) == 3
    assert assets[0] == alpha_token.address
    assert assets[1] == bravo_token.address
    assert assets[2] == charlie_token.address

    # Remove second asset opportunity and verify list is updated
    assert new_mock_lego.removeAssetOpportunity(bravo_token, bravo_token_erc4626_vault, sender=governor)
    assets = new_mock_lego.getAssets()
    assert len(assets) == 2 
    assert assets[0] == alpha_token.address
    assert assets[1] == charlie_token.address

    # Remove remaining opportunities
    assert new_mock_lego.removeAssetOpportunity(alpha_token, alpha_token_erc4626_vault, sender=governor)
    assert new_mock_lego.removeAssetOpportunity(charlie_token, charlie_token_erc4626_vault, sender=governor)
    assert len(new_mock_lego.getAssets()) == 0
