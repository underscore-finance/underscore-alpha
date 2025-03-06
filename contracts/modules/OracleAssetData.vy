# @version 0.4.1

# assets
assets: public(HashMap[uint256, address]) # index -> asset
indexOfAsset: public(HashMap[address, uint256]) # asset -> index
numAssets: public(uint256) # number of assets

MAX_ASSETS: constant(uint256) = 50


@deploy
def __init__():
    pass


#########
# Views #
#########


@view
@external
def getConfiguredAssets() -> DynArray[address, MAX_ASSETS]:
    numAssets: uint256 = self.numAssets
    if numAssets == 0:
        return []
    assets: DynArray[address, MAX_ASSETS] = []
    for i: uint256 in range(1, numAssets, bound=MAX_ASSETS):
        assets.append(self.assets[i])
    return assets


############
# Set Data #
############


@internal
def _addAsset(_asset: address):
    if self.indexOfAsset[_asset] != 0:
        return
    aid: uint256 = self.numAssets
    if aid == 0:
        aid = 1 # not using 0 index
    self.assets[aid] = _asset
    self.indexOfAsset[_asset] = aid
    self.numAssets = aid + 1


@internal
def _removeAsset(_asset: address):
    numAssets: uint256 = self.numAssets
    if numAssets <= 1:
        return

    targetIndex: uint256 = self.indexOfAsset[_asset]
    if targetIndex == 0:
        return

    # update data
    lastIndex: uint256 = numAssets - 1
    self.numAssets = lastIndex
    self.indexOfAsset[_asset] = 0

    # shift to replace the removed one
    if targetIndex != lastIndex:
        lastAsset: address = self.assets[lastIndex]
        self.assets[targetIndex] = lastAsset
        self.indexOfAsset[lastAsset] = targetIndex
