from scripts.deployment.utils import deploy_contract, get_contract, LegoType, Tokens
from utils import log

COMPOUND_V3_CONFIGURATOR = "0x45939657d1CA34A8FA39A924B71D28Fe8431e581"


class VaultTokens:
    USDC = "0xb125E6687d4313864e53df431d5425969c15Eb2F"
    WETH = "0x46e6b214b524310239732D51387075E0e70970bf"
    AERO = "0x784efeB622244d2348d4F2522f8860B96fbEcE89"


def deploy_compoundV3():
    log.h2("Deploying compoundV3...")

    addy_registry = get_contract("AddyRegistry")
    lego_registry = get_contract("LegoRegistry")

    lego_compoundV3 = deploy_contract(
        "CompoundV3",
        "contracts/legos/yield/LegoCompoundV3.vy",
        COMPOUND_V3_CONFIGURATOR,
        addy_registry,
    )

    if lego_registry.isValidNewLegoAddr(lego_compoundV3):
        lego_registry.registerNewLego(lego_compoundV3, "CompoundV3", LegoType.YIELD_OPP)

    log.h2("Adding compoundV3 assets to registry...")

    if len(lego_compoundV3.getAssetOpportunities(Tokens.USDC)) == 0:
        lego_compoundV3.addAssetOpportunity(Tokens.USDC, VaultTokens.USDC)
    if len(lego_compoundV3.getAssetOpportunities(Tokens.WETH)) == 0:
        lego_compoundV3.addAssetOpportunity(Tokens.WETH, VaultTokens.WETH)
    if len(lego_compoundV3.getAssetOpportunities(Tokens.AERO)) == 0:
        lego_compoundV3.addAssetOpportunity(Tokens.AERO, VaultTokens.AERO)

    return lego_compoundV3
