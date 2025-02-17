from scripts.deployment.utils import deploy_contract, get_contract, LegoType, Tokens, remove_contract
from utils import log

SKY_PSM = "0x1601843c5E9bC251A3272907010AFa41Fa18347E"


class VaultTokens:
    USDC = "0x5875eEE11Cf8398102FdAd704C9E96607675467a"
    USDS = "0x5875eEE11Cf8398102FdAd704C9E96607675467a"


def deploy_sky(is_update=False):
    log.h2("Deploying sky...")

    addy_registry = get_contract("AddyRegistry")
    lego_registry = get_contract("LegoRegistry")

    lego_id = 0
    if is_update:
        lego_id = get_contract("Sky").legoId()
        remove_contract("Sky")

    lego_sky = deploy_contract(
        "Sky",
        "contracts/legos/yield/LegoSky.vy",
        SKY_PSM,
        addy_registry,
    )

    print('Sky lego id', lego_id)
    if lego_id == 0:
        if lego_registry.isValidNewLegoAddr(lego_sky):
            lego_registry.registerNewLego(lego_sky, "Sky", LegoType.YIELD_OPP)
    else:
        lego_registry.updateLegoAddr(lego_id, lego_sky)

    return lego_sky
