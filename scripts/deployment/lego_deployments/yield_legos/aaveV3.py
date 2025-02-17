from scripts.deployment.utils import deploy_contract, get_contract, LegoType, Tokens, remove_contract
from utils import log

AAVE_V3_POOL = "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"
AAVE_V3_DATA_PROVIDER = "0xd82a47fdebB5bf5329b09441C3DaB4b5df2153Ad"


class VaultTokens:
    USDC = "0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB"
    WETH = "0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7"
    CBBTC = "0xBdb9300b7CDE636d9cD4AFF00f6F009fFBBc8EE6"
    WSTETH = "0x99CBC45ea5bb7eF3a5BC08FB1B7E56bB2442Ef0D"
    CBETH = "0xcf3D55c10DB69f28fD1A75Bd73f3D8A2d9c595ad"


def deploy_aaveV3(is_update=False):
    log.h2("Deploying aaveV3...")

    addy_registry = get_contract("AddyRegistry")
    lego_registry = get_contract("LegoRegistry")

    lego_id = 0
    if is_update:
        lego_id = get_contract("AaveV3").legoId()
        remove_contract("AaveV3")

    lego_aaveV3 = deploy_contract(
        "AaveV3",
        "contracts/legos/yield/LegoAaveV3.vy",
        AAVE_V3_POOL,
        AAVE_V3_DATA_PROVIDER,
        addy_registry,
    )

    print('AaveV3 lego id', lego_id)

    if lego_id == 0:
        if lego_registry.isValidNewLegoAddr(lego_aaveV3):
            lego_registry.registerNewLego(lego_aaveV3, "AaveV3", LegoType.YIELD_OPP)
    else:
        lego_registry.updateLegoAddr(lego_id, lego_aaveV3)

    log.h2("Adding aaveV3 assets to registry...")

    if len(lego_aaveV3.getAssetOpportunities(Tokens.USDC)) == 0:
        lego_aaveV3.addAssetOpportunity(Tokens.USDC)
    if len(lego_aaveV3.getAssetOpportunities(Tokens.WETH)) == 0:
        lego_aaveV3.addAssetOpportunity(Tokens.WETH)
    if len(lego_aaveV3.getAssetOpportunities(Tokens.CBBTC)) == 0:
        lego_aaveV3.addAssetOpportunity(Tokens.CBBTC)
    if len(lego_aaveV3.getAssetOpportunities(Tokens.WSTETH)) == 0:
        lego_aaveV3.addAssetOpportunity(Tokens.WSTETH)
    if len(lego_aaveV3.getAssetOpportunities(Tokens.CBETH)) == 0:
        lego_aaveV3.addAssetOpportunity(Tokens.CBETH)

    return lego_aaveV3
