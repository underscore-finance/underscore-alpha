from utils.BluePrint import PARAMS, CORE_TOKENS, ADDYS, YIELD_TOKENS


class BluePrint:
    def __init__(self, blueprint):
        self.blueprint = blueprint
        self.PARAMS = PARAMS[blueprint]
        self.CORE_TOKENS = CORE_TOKENS[blueprint]
        self.ADDYS = ADDYS[blueprint]
        self.YIELD_TOKENS = YIELD_TOKENS[blueprint]


class DeployArgs:
    def __init__(self, sender, chain, ignore_logs, blueprint):
        self.sender = sender
        self.chain = chain
        self.ignore_logs = ignore_logs
        self.blueprint = BluePrint(blueprint)


class LegoType:
    YIELD_OPP = 2**0  # 2 ** 0 = 1
    DEX = 2**1  # 2 ** 1 = 2
