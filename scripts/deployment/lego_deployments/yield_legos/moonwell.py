from scripts.deployment.utils import deploy_contract, get_contract, LegoType, Tokens
from utils import log


MOONWELL_COMPTROLLER = "0xfBb21d0380beE3312B33c4353c8936a0F13EF26C"


class VaultTokens:
    USDC = "0xedc817a28e8b93b03976fbd4a3ddbc9f7d176c22"
    WETH = "0x628ff693426583D9a7FB391E54366292F509D457"
    CBBTC = "0xF877ACaFA28c19b96727966690b2f44d35aD5976"
    WSTETH = "0x627fe393bc6edda28e99ae648fd6ff362514304b"
    CBETH = "0x3bf93770f2d4a794c3d9EBEfBAeBAE2a8f09A5E5"
    AERO = "0x73902f619CEB9B31FD8EFecf435CbDf89E369Ba6"


def deploy_moonwell():
    log.h2("Deploying moonwell...")

    addy_registry = get_contract("AddyRegistry")
    lego_registry = get_contract("LegoRegistry")

    lego_moonwell = deploy_contract(
        "Moonwell",
        "contracts/legos/yield/LegoMoonwell.vy",
        MOONWELL_COMPTROLLER,
        addy_registry,
    )

    if lego_registry.isValidNewLegoAddr(lego_moonwell):
        lego_registry.registerNewLego(lego_moonwell, "Moonwell", LegoType.YIELD_OPP)

    log.h2("Adding moonwell assets to registry...")

    if len(lego_moonwell.getAssetOpportunities(Tokens.USDC)) == 0:
        lego_moonwell.addAssetOpportunity(Tokens.USDC, VaultTokens.USDC)
    if len(lego_moonwell.getAssetOpportunities(Tokens.WETH)) == 0:
        lego_moonwell.addAssetOpportunity(Tokens.WETH, VaultTokens.WETH)
    if len(lego_moonwell.getAssetOpportunities(Tokens.CBBTC)) == 0:
        lego_moonwell.addAssetOpportunity(Tokens.CBBTC, VaultTokens.CBBTC)
    if len(lego_moonwell.getAssetOpportunities(Tokens.WSTETH)) == 0:
        lego_moonwell.addAssetOpportunity(Tokens.WSTETH, VaultTokens.WSTETH)
    if len(lego_moonwell.getAssetOpportunities(Tokens.CBETH)) == 0:
        lego_moonwell.addAssetOpportunity(Tokens.CBETH, VaultTokens.CBETH)
    if len(lego_moonwell.getAssetOpportunities(Tokens.AERO)) == 0:
        lego_moonwell.addAssetOpportunity(Tokens.AERO, VaultTokens.AERO)

    return lego_moonwell
