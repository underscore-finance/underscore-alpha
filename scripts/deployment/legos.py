from scripts.deployment.utils import deploy_contract, get_contract
from scripts.deployment.lego_deployments.yield_legos.aaveV3 import deploy_aaveV3
from scripts.deployment.lego_deployments.yield_legos.compoundV3 import deploy_compoundV3
from scripts.deployment.lego_deployments.yield_legos.euler import deploy_euler
from scripts.deployment.lego_deployments.yield_legos.fluid import deploy_fluid
from scripts.deployment.lego_deployments.yield_legos.morpho import deploy_morpho
from scripts.deployment.lego_deployments.yield_legos.moonwell import deploy_moonwell
from scripts.deployment.lego_deployments.yield_legos.sky import deploy_sky

from utils import log


def deploy_legos():
    log.h1("Deploying legos...")

    addy_registry = get_contract('AddyRegistry')

    lego_aaveV3 = deploy_aaveV3()
    lego_compoundV3 = deploy_compoundV3()
    lego_euler = deploy_euler()
    lego_fluid = deploy_fluid()
    lego_moonwell = deploy_moonwell()
    lego_morpho = deploy_morpho()
    lego_sky = deploy_sky()

    deploy_contract(
        'LegoHelper',
        'contracts/core/LegoHelper.vy',
        addy_registry,
        lego_aaveV3.id(),
        lego_compoundV3.id(),
        lego_euler.id(),
        lego_fluid.id(),
        lego_moonwell.id(),
        lego_morpho.id(),
        lego_sky.id(),
    )
