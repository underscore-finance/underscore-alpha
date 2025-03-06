# PriceSheets

The PriceSheets contract handles price data management and calculations for both transaction fees and subscription pricing.

**Source:** `contracts/core/PriceSheets.vy`

## Structs

### TxPriceSheet

```vyper
struct TxPriceSheet:
    depositFee: uint256
    withdrawalFee: uint256
    rebalanceFee: uint256
    transferFee: uint256
    swapFee: uint256
    addLiqFee: uint256
    removeLiqFee: uint256
    claimRewardsFee: uint256
    borrowFee: uint256
    repayFee: uint256
```

Structure containing fee percentages for different transaction types.

### SubscriptionInfo

```vyper
struct SubscriptionInfo:
    asset: address
    usdValue: uint256
    trialPeriod: uint256
    payPeriod: uint256
```

Structure containing subscription pricing information.

### SubPaymentInfo

```vyper
struct SubPaymentInfo:
    recipient: address
    asset: address
    amount: uint256
    usdValue: uint256
    paidThroughBlock: uint256
    didChange: bool
```

Structure containing subscription payment details.

### PendingSubPrice

```vyper
struct PendingSubPrice:
    subInfo: SubscriptionInfo
    effectiveBlock: uint256
```

Structure containing pending subscription price changes.

## Events

### AgentSubPriceSet

```vyper
event AgentSubPriceSet:
    agent: indexed(address)
    asset: indexed(address)
    usdValue: uint256
    trialPeriod: uint256
    payPeriod: uint256
```

Emitted when subscription pricing is set for an agent.

### PendingAgentSubPriceSet

```vyper
event PendingAgentSubPriceSet:
    agent: indexed(address)
    asset: indexed(address)
    usdValue: uint256
    trialPeriod: uint256
    payPeriod: uint256
    effectiveBlock: uint256
```

Emitted when pending subscription pricing is set for an agent.

### ProtocolSubPriceSet

```vyper
event ProtocolSubPriceSet:
    asset: indexed(address)
    usdValue: uint256
    trialPeriod: uint256
    payPeriod: uint256
```

Emitted when subscription pricing is set for the protocol.

### AgentSubPriceRemoved

```vyper
event AgentSubPriceRemoved:
    agent: indexed(address)
    asset: indexed(address)
    usdValue: uint256
    trialPeriod: uint256
    payPeriod: uint256
```

Emitted when subscription pricing is removed for an agent.

### ProtocolSubPriceRemoved

```vyper
event ProtocolSubPriceRemoved:
    asset: indexed(address)
    usdValue: uint256
    trialPeriod: uint256
    payPeriod: uint256
```

Emitted when subscription pricing is removed for the protocol.

### AgentSubPricingEnabled

```vyper
event AgentSubPricingEnabled:
    isEnabled: bool
```

Emitted when agent subscription pricing is enabled or disabled.

### ProtocolTxPriceSheetSet

```vyper
event ProtocolTxPriceSheetSet:
    depositFee: uint256
    withdrawalFee: uint256
    rebalanceFee: uint256
    transferFee: uint256
    swapFee: uint256
    addLiqFee: uint256
    removeLiqFee: uint256
    claimRewardsFee: uint256
    borrowFee: uint256
    repayFee: uint256
```

Emitted when transaction pricing is set for the protocol.

### ProtocolTxPriceSheetRemoved

```vyper
event ProtocolTxPriceSheetRemoved:
    depositFee: uint256
    withdrawalFee: uint256
    rebalanceFee: uint256
    transferFee: uint256
    swapFee: uint256
    addLiqFee: uint256
    removeLiqFee: uint256
    claimRewardsFee: uint256
    borrowFee: uint256
    repayFee: uint256
```

Emitted when transaction pricing is removed for the protocol.

### ProtocolRecipientSet

```vyper
event ProtocolRecipientSet:
    recipient: indexed(address)
```

Emitted when the protocol fee recipient is set.

### PriceChangeDelaySet

```vyper
event PriceChangeDelaySet:
    delayBlocks: uint256
```

Emitted when the price change delay is set.

### PriceSheetsActivated

```vyper
event PriceSheetsActivated:
    isActivated: bool
```

Emitted when the price sheets contract is activated or deactivated.

## Storage Variables

### protocolRecipient

```vyper
protocolRecipient: public(address)
```

The address that receives protocol fees.

### protocolTxPriceData

```vyper
protocolTxPriceData: public(TxPriceSheet)
```

Transaction pricing data for the protocol.

### protocolSubPriceData

```vyper
protocolSubPriceData: public(SubscriptionInfo)
```

Subscription pricing data for the protocol.

### isAgentSubPricingEnabled

```vyper
isAgentSubPricingEnabled: public(bool)
```

Flag indicating whether agent subscription pricing is enabled.

### agentSubPriceData

```vyper
agentSubPriceData: public(HashMap[address, SubscriptionInfo])
```

Mapping from agent address to subscription pricing data.

### pendingAgentSubPrices

```vyper
pendingAgentSubPrices: public(HashMap[address, PendingSubPrice])
```

Mapping from agent address to pending subscription price changes.

### priceChangeDelay

```vyper
priceChangeDelay: public(uint256)
```

Number of blocks that must pass before price changes take effect.

### ADDY_REGISTRY

```vyper
ADDY_REGISTRY: public(immutable(address))
```

Address of the address registry.

### isActivated

```vyper
isActivated: public(bool)
```

Flag indicating whether the price sheets contract is activated.

### MIN_TRIAL_PERIOD

```vyper
MIN_TRIAL_PERIOD: public(immutable(uint256))
```

Minimum allowed trial period in blocks.

### MAX_TRIAL_PERIOD

```vyper
MAX_TRIAL_PERIOD: public(immutable(uint256))
```

Maximum allowed trial period in blocks.

### MIN_PAY_PERIOD

```vyper
MIN_PAY_PERIOD: public(immutable(uint256))
```

Minimum allowed payment period in blocks.

### MAX_PAY_PERIOD

```vyper
MAX_PAY_PERIOD: public(immutable(uint256))
```

Maximum allowed payment period in blocks.

### MIN_PRICE_CHANGE_BUFFER

```vyper
MIN_PRICE_CHANGE_BUFFER: public(immutable(uint256))
```

Minimum allowed price change buffer in blocks.

## Constants

### AGENT_FACTORY_ID

```vyper
AGENT_FACTORY_ID: constant(uint256) = 1
```

ID of the agent factory in the address registry.

### MAX_TX_FEE

```vyper
MAX_TX_FEE: constant(uint256) = 10_00 # 10.00%
```

Maximum allowed transaction fee percentage (10.00%).

## External Functions

### getAgentSubPriceData

```vyper
@view
@external
def getAgentSubPriceData(_agent: address) -> SubscriptionInfo:
```

Gets subscription price data for an agent.

**Parameters:**
- `_agent`: The address of the agent

**Returns:**
- Subscription information for the agent

**Requirements:**
- Returns empty SubscriptionInfo if agent subscription pricing is disabled

### protocolSubPriceData

```vyper
@view
@external
def protocolSubPriceData() -> SubscriptionInfo:
```

Gets subscription price data for the protocol.

**Returns:**
- Subscription information for the protocol

### getCombinedSubData

```vyper
@view
@external
def getCombinedSubData(_user: address, _agent: address, _agentPaidThru: uint256, _protocolPaidThru: uint256, _oracleRegistry: address) -> (SubPaymentInfo, SubPaymentInfo):
```

Gets combined subscription data for a user and agent.

**Parameters:**
- `_user`: The address of the user
- `_agent`: The address of the agent
- `_agentPaidThru`: The block until which the agent subscription is paid
- `_protocolPaidThru`: The block until which the protocol subscription is paid
- `_oracleRegistry`: The address of the oracle registry

**Returns:**
- Tuple containing subscription payment information for agent and protocol

### isValidSubPrice

```vyper
@view
@external
def isValidSubPrice(_asset: address, _usdValue: uint256, _trialPeriod: uint256, _payPeriod: uint256) -> bool:
```

Checks if subscription price parameters are valid.

**Parameters:**
- `_asset`: The token address for subscription payments
- `_usdValue`: The USD value of the subscription
- `_trialPeriod`: The trial period in blocks
- `_payPeriod`: The payment period in blocks

**Returns:**
- True if all parameters are valid, False otherwise

### setAgentSubPrice

```vyper
@external
def setAgentSubPrice(_agent: address, _asset: address, _usdValue: uint256, _trialPeriod: uint256, _payPeriod: uint256) -> bool:
```

Sets subscription pricing for a specific agent.

**Parameters:**
- `_agent`: The address of the agent
- `_asset`: The token address for subscription payments
- `_usdValue`: The USD value of the subscription
- `_trialPeriod`: The trial period in blocks
- `_payPeriod`: The payment period in blocks

**Returns:**
- True if pending subscription price was set successfully

**Events Emitted:**
- `AgentSubPriceSet` or `PendingAgentSubPriceSet`

**Requirements:**
- Agent must be registered
- Caller must be the agent owner or governor
- If caller is agent owner, price sheets must be activated
- Agent address must be valid
- Subscription price parameters must be valid

### finalizePendingAgentSubPrice

```vyper
@external
def finalizePendingAgentSubPrice(_agent: address) -> bool:
```

Finalizes a pending subscription price for an agent.

**Parameters:**
- `_agent`: The address of the agent

**Returns:**
- True if subscription price was finalized successfully

**Events Emitted:**
- `AgentSubPriceSet`

**Requirements:**
- Price sheets must be activated
- Price change delay must have passed

### removeAgentSubPrice

```vyper
@external
def removeAgentSubPrice(_agent: address) -> bool:
```

Removes subscription pricing for a specific agent.

**Parameters:**
- `_agent`: The address of the agent

**Returns:**
- True if agent subscription price was removed successfully

**Events Emitted:**
- `AgentSubPriceRemoved`

**Requirements:**
- Caller must be the governor
- Agent must be registered
- Agent must have subscription pricing set

### setAgentSubPricingEnabled

```vyper
@external
def setAgentSubPricingEnabled(_isEnabled: bool) -> bool:
```

Enables or disables agent subscription pricing.

**Parameters:**
- `_isEnabled`: True to enable, False to disable

**Returns:**
- True if agent subscription pricing state was changed successfully

**Events Emitted:**
- `AgentSubPricingEnabled`

**Requirements:**
- Caller must be the governor
- New state must be different from current state

### setProtocolSubPrice

```vyper
@external
def setProtocolSubPrice(_asset: address, _usdValue: uint256, _trialPeriod: uint256, _payPeriod: uint256) -> bool:
```

Sets subscription pricing for the protocol.

**Parameters:**
- `_asset`: The token address for subscription payments
- `_usdValue`: The USD value of the subscription
- `_trialPeriod`: The trial period in blocks
- `_payPeriod`: The payment period in blocks

**Returns:**
- True if protocol subscription price was set successfully

**Events Emitted:**
- `ProtocolSubPriceSet`

**Requirements:**
- Caller must be the governor
- Subscription price parameters must be valid

### removeProtocolSubPrice

```vyper
@external
def removeProtocolSubPrice() -> bool:
```

Removes subscription pricing for the protocol.

**Returns:**
- True if protocol subscription price was removed successfully

**Events Emitted:**
- `ProtocolSubPriceRemoved`

**Requirements:**
- Caller must be the governor
- Protocol must have subscription pricing set

### getTransactionFeeData

```vyper
@view
@external
def getTransactionFeeData(_user: address, _action: ActionType) -> (uint256, address):
```

Gets transaction fee data for the protocol.

**Parameters:**
- `_user`: The address of the user
- `_action`: The type of action being performed

**Returns:**
- Tuple containing the fee amount and recipient address for the protocol

### isValidTxPriceSheet

```vyper
@view
@external
def isValidTxPriceSheet(
    _depositFee: uint256,
    _withdrawalFee: uint256,
    _rebalanceFee: uint256,
    _transferFee: uint256,
    _swapFee: uint256,
    _addLiqFee: uint256,
    _removeLiqFee: uint256,
    _claimRewardsFee: uint256,
    _borrowFee: uint256,
    _repayFee: uint256,
) -> bool:
```

Checks if transaction price sheet parameters are valid.

**Parameters:**
- `_depositFee`: The fee percentage for deposits
- `_withdrawalFee`: The fee percentage for withdrawals
- `_rebalanceFee`: The fee percentage for rebalances
- `_transferFee`: The fee percentage for transfers
- `_swapFee`: The fee percentage for swaps
- `_addLiqFee`: The fee percentage for adding liquidity
- `_removeLiqFee`: The fee percentage for removing liquidity
- `_claimRewardsFee`: The fee percentage for claiming rewards
- `_borrowFee`: The fee percentage for borrowing
- `_repayFee`: The fee percentage for repaying

**Returns:**
- True if all parameters are valid, False otherwise

### setProtocolTxPriceSheet

```vyper
@external
def setProtocolTxPriceSheet(
    _depositFee: uint256,
    _withdrawalFee: uint256,
    _rebalanceFee: uint256,
    _transferFee: uint256,
    _swapFee: uint256,
    _addLiqFee: uint256,
    _removeLiqFee: uint256,
    _claimRewardsFee: uint256,
    _borrowFee: uint256,
    _repayFee: uint256,
) -> bool:
```

Sets transaction price sheet for the protocol.

**Parameters:**
- `_depositFee`: The fee percentage for deposits
- `_withdrawalFee`: The fee percentage for withdrawals
- `_rebalanceFee`: The fee percentage for rebalances
- `_transferFee`: The fee percentage for transfers
- `_swapFee`: The fee percentage for swaps
- `_addLiqFee`: The fee percentage for adding liquidity
- `_removeLiqFee`: The fee percentage for removing liquidity
- `_claimRewardsFee`: The fee percentage for claiming rewards
- `_borrowFee`: The fee percentage for borrowing
- `_repayFee`: The fee percentage for repaying

**Returns:**
- True if protocol price sheet was set successfully

**Events Emitted:**
- `ProtocolTxPriceSheetSet`

**Requirements:**
- Caller must be the governor
- Transaction price sheet parameters must be valid

### removeProtocolTxPriceSheet

```vyper
@external
def removeProtocolTxPriceSheet() -> bool:
```

Removes transaction price sheet for the protocol.

**Returns:**
- True if protocol price sheet was removed successfully

**Events Emitted:**
- `ProtocolTxPriceSheetRemoved`

**Requirements:**
- Caller must be the governor

### setProtocolRecipient

```vyper
@external
def setProtocolRecipient(_recipient: address) -> bool:
```

Sets the recipient address for protocol fees.

**Parameters:**
- `_recipient`: The address to receive protocol fees

**Returns:**
- True if protocol recipient was set successfully

**Events Emitted:**
- `ProtocolRecipientSet`

**Requirements:**
- Caller must be the governor
- Recipient address must be valid

### setPriceChangeDelay

```vyper
@external
def setPriceChangeDelay(_delayBlocks: uint256) -> bool:
```

Sets the number of blocks required before price changes take effect.

**Parameters:**
- `_delayBlocks`: The number of blocks to wait before price changes take effect

**Returns:**
- True if price change delay was set successfully

**Events Emitted:**
- `PriceChangeDelaySet`

**Requirements:**
- Caller must be the governor
- Delay must be 0 or greater than or equal to MIN_PRICE_CHANGE_BUFFER

### activate

```vyper
@external
def activate(_shouldActivate: bool):
```

Activates or deactivates the price sheets registry.

**Parameters:**
- `_shouldActivate`: True to activate, False to deactivate

**Events Emitted:**
- `PriceSheetsActivated`

**Requirements:**
- Caller must be the governor 