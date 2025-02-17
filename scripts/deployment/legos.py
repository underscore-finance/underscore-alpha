from scripts.deployment.utils import deploy_contract, get_contract, remove_contract
from scripts.deployment.lego_deployments.yield_legos.aaveV3 import deploy_aaveV3
from scripts.deployment.lego_deployments.yield_legos.compoundV3 import deploy_compoundV3
from scripts.deployment.lego_deployments.yield_legos.euler import deploy_euler
from scripts.deployment.lego_deployments.yield_legos.fluid import deploy_fluid
from scripts.deployment.lego_deployments.yield_legos.morpho import deploy_morpho
from scripts.deployment.lego_deployments.yield_legos.moonwell import deploy_moonwell
from scripts.deployment.lego_deployments.yield_legos.sky import deploy_sky

from utils import log


def deploy_legos(is_update=False):
    log.h1("Deploying legos...")

    addy_registry = get_contract('AddyRegistry')

    lego_aaveV3 = deploy_aaveV3(is_update)
    lego_compoundV3 = deploy_compoundV3(is_update)
    lego_euler = deploy_euler(is_update)
    lego_fluid = deploy_fluid(is_update)
    lego_moonwell = deploy_moonwell(is_update)
    lego_morpho = deploy_morpho(is_update)
    lego_sky = deploy_sky(is_update)

    if is_update:
        remove_contract('LegoHelper')

    deploy_contract(
        'LegoHelper',
        'contracts/core/LegoHelper.vy',
        addy_registry,
        lego_aaveV3.legoId(),
        lego_compoundV3.legoId(),
        lego_euler.legoId(),
        lego_fluid.legoId(),
        lego_moonwell.legoId(),
        lego_morpho.legoId(),
        lego_sky.legoId(),
    )
