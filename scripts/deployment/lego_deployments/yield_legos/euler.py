from scripts.deployment.utils import deploy_contract, get_contract, LegoType, Tokens, remove_contract
from utils import log


EULER_FACTORY = "0x7F321498A801A191a93C840750ed637149dDf8D0"
EARN_FACTORY = "0x72bbDB652F2AEC9056115644EfCcDd1986F51f15"


class VaultTokens:
    USDC = "0x0A1a3b5f2041F33522C4efc754a7D096f880eE16"
    WETH = "0x859160DB5841E5cfB8D3f144C6b3381A85A4b410"
    EURC = "0x9ECD9fbbdA32b81dee51AdAed28c5C5039c87117"
    CBBTC = "0x882018411Bc4A020A879CEE183441fC9fa5D7f8B"


def deploy_euler(is_update=False):
    log.h2("Deploying euler...")

    addy_registry = get_contract("AddyRegistry")
    lego_registry = get_contract("LegoRegistry")

    lego_id = 0
    if is_update:
        lego_id = get_contract("Euler").legoId()
        remove_contract("Euler")

    lego_euler = deploy_contract(
        "Euler",
        "contracts/legos/yield/LegoEuler.vy",
        EULER_FACTORY,
        EARN_FACTORY,
        addy_registry,
    )

    print('Euler lego id', lego_id)
    if lego_id == 0:
        if lego_registry.isValidNewLegoAddr(lego_euler):
            lego_registry.registerNewLego(lego_euler, "Euler", LegoType.YIELD_OPP)
    else:
        lego_registry.updateLegoAddr(lego_id, lego_euler)

    log.h2("Adding euler assets to registry...")

    if len(lego_euler.getAssetOpportunities(Tokens.USDC)) == 0:
        lego_euler.addAssetOpportunity(Tokens.USDC, VaultTokens.USDC)
    if len(lego_euler.getAssetOpportunities(Tokens.WETH)) == 0:
        lego_euler.addAssetOpportunity(Tokens.WETH, VaultTokens.WETH)
    if len(lego_euler.getAssetOpportunities(Tokens.EURC)) == 0:
        lego_euler.addAssetOpportunity(Tokens.EURC, VaultTokens.EURC)
    if len(lego_euler.getAssetOpportunities(Tokens.CBBTC)) == 0:
        lego_euler.addAssetOpportunity(Tokens.CBBTC, VaultTokens.CBBTC)

    return lego_euler
