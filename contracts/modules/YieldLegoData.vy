# @version 0.4.0

event AssetOpportunityAdded:
    asset: indexed(address)
    vaultToken: indexed(address)

event AssetOpportunityRemoved:
    asset: indexed(address)
    vaultToken: indexed(address)

# asset opportunities
assetOpportunities: public(HashMap[address, HashMap[uint256, address]]) # asset -> index -> vault token
indexOfAssetOpportunity: public(HashMap[address, HashMap[address, uint256]]) # asset -> vault token -> index
numAssetOpportunities: public(HashMap[address, uint256]) # asset -> number of opportunities
vaultToAsset: public(HashMap[address, address]) # vault token -> asset

# assets
assets: public(HashMap[uint256, address]) # index -> asset
indexOfAsset: public(HashMap[address, uint256]) # asset -> index
numAssets: public(uint256) # number of assets

MAX_VAULTS: constant(uint256) = 15
MAX_ASSETS: constant(uint256) = 25


@deploy
def __init__():
    pass


#########
# Views #
#########


@view
@external
def getAssetOpportunities(_asset: address) -> DynArray[address, MAX_VAULTS]:
    numOpportunities: uint256 = self.numAssetOpportunities[_asset]
    if numOpportunities == 0:
        return []
    opportunities: DynArray[address, MAX_VAULTS] = []
    for i: uint256 in range(1, numOpportunities, bound=MAX_VAULTS):
        opportunities.append(self.assetOpportunities[_asset][i])
    return opportunities


@view
@external
def getAssets() -> DynArray[address, MAX_ASSETS]:
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
def _addAssetOpportunity(_asset: address, _vault: address):
    assert self.indexOfAssetOpportunity[_asset][_vault] == 0 # dev: asset + vault token already added
    assert empty(address) not in [_asset, _vault] # dev: invalid addresses

    aid: uint256 = self.numAssetOpportunities[_asset]
    if aid == 0:
        aid = 1 # not using 0 index
    self.assetOpportunities[_asset][aid] = _vault
    self.indexOfAssetOpportunity[_asset][_vault] = aid
    self.numAssetOpportunities[_asset] = aid + 1
    self.vaultToAsset[_vault] = _asset

    # add asset
    self._addAsset(_asset)

    log AssetOpportunityAdded(_asset, _vault)


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
def _removeAssetOpportunity(_asset: address, _vault: address):
    targetIndex: uint256 = self.indexOfAssetOpportunity[_asset][_vault]
    assert targetIndex != 0 # dev: asset + vault token not found

    numOpportunities: uint256 = self.numAssetOpportunities[_asset]
    assert numOpportunities > 1 # dev: no opportunities to remove

    # update data
    lastIndex: uint256 = numOpportunities - 1
    self.numAssetOpportunities[_asset] = lastIndex
    self.indexOfAssetOpportunity[_asset][_vault] = 0
    self.vaultToAsset[_vault] = empty(address)

    # shift to replace the removed one
    if targetIndex != lastIndex:
        lastVaultToken: address = self.assetOpportunities[_asset][lastIndex]
        self.assetOpportunities[_asset][targetIndex] = lastVaultToken
        self.indexOfAssetOpportunity[_asset][lastVaultToken] = targetIndex

    # remove asset
    if lastIndex <= 1:
        self._removeAsset(_asset)

    log AssetOpportunityRemoved(_asset, _vault)


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
