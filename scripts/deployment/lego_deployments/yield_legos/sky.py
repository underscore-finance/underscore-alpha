from scripts.deployment.utils import deploy_contract, get_contract, LegoType, Tokens
from utils import log

SKY_PSM = "0x1601843c5E9bC251A3272907010AFa41Fa18347E"


class VaultTokens:
    USDC = "0x5875eEE11Cf8398102FdAd704C9E96607675467a"
    USDS = "0x5875eEE11Cf8398102FdAd704C9E96607675467a"


def deploy_sky():
    log.h2("Deploying sky...")

    addy_registry = get_contract("AddyRegistry")
    lego_registry = get_contract("LegoRegistry")

    lego_sky = deploy_contract(
        "Sky",
        "contracts/legos/yield/LegoSky.vy",
        SKY_PSM,
        addy_registry,
    )

    if lego_registry.isValidNewLegoAddr(lego_sky):
        lego_registry.registerNewLego(lego_sky, "Sky", LegoType.YIELD_OPP)

    return lego_sky
