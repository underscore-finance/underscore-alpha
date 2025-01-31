# @version 0.4.0

struct ChainlinkRound:
    roundId: uint80
    answer: int256
    startedAt: uint256
    updatedAt: uint256
    answeredInRound: uint80

mockData: ChainlinkRound


@deploy
def __init__(_localPrice: uint256):
    if _localPrice != 0:
        self.mockData = ChainlinkRound(
            roundId=1,
            answer=convert(_localPrice // (10 ** 10), int256),
            startedAt=block.timestamp,
            updatedAt=block.timestamp,
            answeredInRound=1,
        )


@view 
@external 
def latestRoundData() -> ChainlinkRound:
    return self.mockData


@view
@external
def decimals() -> uint8:
    return 8


@external
def setMockData(
    _price: int256,
    _roundId: uint80 = 1,
    _answeredInRound: uint80 = 1,
    _startedAt: uint256 = block.timestamp,
    _updatedAt: uint256 = block.timestamp,
):
    self.mockData = ChainlinkRound(
        roundId=_roundId,
        answer=_price,
        startedAt=_startedAt,
        updatedAt=_updatedAt,
        answeredInRound=_answeredInRound,
    )