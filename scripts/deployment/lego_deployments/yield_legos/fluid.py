from scripts.deployment.utils import deploy_contract, get_contract, LegoType, Tokens
from utils import log


FLUID_RESOLVER = "0x3aF6FBEc4a2FE517F56E402C65e3f4c3e18C1D86"


class VaultTokens:
    USDC = "0xf42f5795D9ac7e9D757dB633D693cD548Cfd9169"
    WETH = "0x9272D6153133175175Bc276512B2336BE3931CE9"
    WSTETH = "0x896E39f0E9af61ECA9dD2938E14543506ef2c2b5"
    EURC = "0x1943FA26360f038230442525Cf1B9125b5DCB401"


def deploy_fluid():
    log.h2("Deploying fluid...")

    addy_registry = get_contract("AddyRegistry")
    lego_registry = get_contract("LegoRegistry")

    lego_fluid = deploy_contract(
        "Fluid",
        "contracts/legos/yield/LegoFluid.vy",
        FLUID_RESOLVER,
        addy_registry,
    )

    if lego_registry.isValidNewLegoAddr(lego_fluid):
        lego_registry.registerNewLego(lego_fluid, "Fluid", LegoType.YIELD_OPP)

    log.h2("Adding fluid assets to registry...")

    if len(lego_fluid.getAssetOpportunities(Tokens.USDC)) == 0:
        lego_fluid.addAssetOpportunity(Tokens.USDC, VaultTokens.USDC)
    if len(lego_fluid.getAssetOpportunities(Tokens.WETH)) == 0:
        lego_fluid.addAssetOpportunity(Tokens.WETH, VaultTokens.WETH)
    if len(lego_fluid.getAssetOpportunities(Tokens.WSTETH)) == 0:
        lego_fluid.addAssetOpportunity(Tokens.WSTETH, VaultTokens.WSTETH)
    if len(lego_fluid.getAssetOpportunities(Tokens.EURC)) == 0:
        lego_fluid.addAssetOpportunity(Tokens.EURC, VaultTokens.EURC)

    return lego_fluid
