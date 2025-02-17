from scripts.deployment.utils import deploy_contract, get_contract, LegoType, Tokens, remove_contract
from utils import log

MORPHO_FACTORY = "0xFf62A7c278C62eD665133147129245053Bbf5918"
MORPHO_FACTORY_LEGACY = "0xA9c3D3a366466Fa809d1Ae982Fb2c46E5fC41101"


class VaultTokens:
    USDC = "0xc1256ae5ff1cf2719d4937adb3bbccab2e00a2ca"
    WETH = "0xa0E430870c4604CcfC7B38Ca7845B1FF653D0ff1"
    EURC = "0xf24608E0CCb972b0b0f4A6446a0BBf58c701a026"
    CBBTC = "0x543257eF2161176D7C8cD90BA65C2d4CaEF5a796"


def deploy_morpho(is_update=False):
    log.h2("Deploying morpho...")

    addy_registry = get_contract("AddyRegistry")
    lego_registry = get_contract("LegoRegistry")

    lego_id = 0
    if is_update:
        lego_id = get_contract("Morpho").legoId()
        remove_contract("Morpho")

    lego_morpho = deploy_contract(
        "Morpho",
        "contracts/legos/yield/LegoMorpho.vy",
        MORPHO_FACTORY,
        MORPHO_FACTORY_LEGACY,
        addy_registry,
    )

    print('Morpho lego id', lego_id)
    if lego_id == 0:
        if lego_registry.isValidNewLegoAddr(lego_morpho):
            lego_registry.registerNewLego(lego_morpho, "Morpho", LegoType.YIELD_OPP)
    else:
        lego_registry.updateLegoAddr(lego_id, lego_morpho)

    log.h2("Adding moonwell assets to registry...")

    if len(lego_morpho.getAssetOpportunities(Tokens.USDC)) == 0:
        lego_morpho.addAssetOpportunity(Tokens.USDC, VaultTokens.USDC)
    if len(lego_morpho.getAssetOpportunities(Tokens.WETH)) == 0:
        lego_morpho.addAssetOpportunity(Tokens.WETH, VaultTokens.WETH)
    if len(lego_morpho.getAssetOpportunities(Tokens.EURC)) == 0:
        lego_morpho.addAssetOpportunity(Tokens.EURC, VaultTokens.EURC)
    if len(lego_morpho.getAssetOpportunities(Tokens.CBBTC)) == 0:
        lego_morpho.addAssetOpportunity(Tokens.CBBTC, VaultTokens.CBBTC)

    return lego_morpho
