# PriceSheets

The PriceSheets contract handles price data management and calculations for both transaction fees and subscription pricing.

**Source:** `contracts/core/PriceSheets.vy`

## Flags

### ActionType

```vyper
flag ActionType:
    DEPOSIT
    WITHDRAWAL
    REBALANCE
    TRANSFER
    SWAP
    CONVERSION
    ADD_LIQ
    REMOVE_LIQ
    CLAIM_REWARDS
    BORROW
    REPAY
```

Flag defining the types of actions for which fees can be charged.

## Structs

### TxPriceSheet

```vyper
struct TxPriceSheet:
    yieldFee: uint256
    swapFee: uint256
    claimRewardsFee: uint256
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
    yieldFee: uint256
    swapFee: uint256
    claimRewardsFee: uint256
```

Emitted when transaction pricing is set for the protocol.

### ProtocolTxPriceSheetRemoved

```vyper
event ProtocolTxPriceSheetRemoved:
    yieldFee: uint256
    swapFee: uint256
    claimRewardsFee: uint256
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

### AmbassadorRatioSet

```vyper
event AmbassadorRatioSet:
    ratio: uint256
```

Emitted when the ambassador ratio is set.

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

### ambassadorRatio

```vyper
ambassadorRatio: public(uint256)
```

Ratio of transaction fees that go to ambassadors.

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

### HUNDRED_PERCENT

```vyper
HUNDRED_PERCENT: constant(uint256) = 100_00 # 100.00%
```

Represents 100.00% in basis points.

### MAX_TX_FEE

```vyper
MAX_TX_FEE: constant(uint256) = 20_00 # 20.00%
```

Maximum allowed transaction fee percentage (20.00%).

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

### getCombinedSubData

```vyper
@view
@external
def getCombinedSubData(_user: address, _agent: address, _agentPaidThru: uint256, _protocolPaidThru: uint256, _oracleRegistry: address) -> (SubPaymentInfo, SubPaymentInfo):
```

Gets combined subscription data for an agent and protocol.

**Parameters:**

- `_user`: The address of the user
- `_agent`: The address of the agent
- `_agentPaidThru`: The block until which the agent subscription is paid
- `_protocolPaidThru`: The block until which the protocol subscription is paid
- `_oracleRegistry`: The address of the oracle registry

**Returns:**

- Tuple containing subscription payment information for protocol and agent

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

**Requirements:**

- Agent must be registered
- Caller must be the agent owner or governor
- If caller is agent owner, price sheets must be activated
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

**Requirements:**

- Price sheets must be activated
- A pending subscription price must exist for the agent
- The effective block for the price change must have been reached

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

**Requirements:**

- Caller must be authorized to govern
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

**Requirements:**

- Caller must be authorized to govern
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

**Requirements:**

- Caller must be authorized to govern
- Subscription price parameters must be valid

### removeProtocolSubPrice

```vyper
@external
def removeProtocolSubPrice() -> bool:
```

Removes subscription pricing for the protocol.

**Parameters:**

- None

**Returns:**

- True if protocol subscription price was removed successfully

**Requirements:**

- Caller must be authorized to govern
- Protocol must have subscription pricing set

### getTransactionFeeDataWithAmbassadorRatio

```vyper
@view
@external
def getTransactionFeeDataWithAmbassadorRatio(_user: address, _action: ActionType) -> (uint256, address, uint256):
```

Gets transaction fee data with ambassador ratio for a user and action.

**Parameters:**

- `_user`: The address of the user
- `_action`: The type of action being performed

**Returns:**

- Tuple containing the fee amount, recipient address, and ambassador ratio

### getTransactionFeeData

```vyper
@view
@external
def getTransactionFeeData(_user: address, _action: ActionType) -> (uint256, address):
```

Gets transaction fee data for a user and action (legacy function).

**Parameters:**

- `_user`: The address of the user
- `_action`: The type of action being performed

**Returns:**

- Tuple containing the fee amount and recipient address

### setProtocolTxPriceSheet

```vyper
@external
def setProtocolTxPriceSheet(_yield: uint256, _swap: uint256, _claimRewards: uint256) -> bool:
```

Sets transaction pricing for the protocol.

**Parameters:**

- `_yield`: The fee percentage for yield operations
- `_swap`: The fee percentage for swap operations
- `_claimRewards`: The fee percentage for claiming rewards

**Returns:**

- True if protocol transaction pricing was set successfully

**Requirements:**

- Caller must be authorized to govern
- Fee percentages must be within allowed range

### setProtocolRecipient

```vyper
@external
def setProtocolRecipient(_recipient: address) -> bool:
```

Sets the recipient for protocol fees.

**Parameters:**

- `_recipient`: The address to receive protocol fees

**Returns:**

- True if protocol recipient was set successfully

**Requirements:**

- Caller must be authorized to govern
- Recipient address must not be empty

### setPriceChangeDelay

```vyper
@external
def setPriceChangeDelay(_delayBlocks: uint256) -> bool:
```

Sets the delay for price changes to take effect.

**Parameters:**

- `_delayBlocks`: The delay period in blocks

**Returns:**

- True if price change delay was set successfully

**Requirements:**

- Caller must be authorized to govern
- Delay must be at least the minimum price change buffer

### setAmbassadorRatio

```vyper
@external
def setAmbassadorRatio(_ratio: uint256) -> bool:
```

Sets the ratio of transaction fees that go to ambassadors.

**Parameters:**

- `_ratio`: The ratio value (percentage in basis points)

**Returns:**

- True if ambassador ratio was set successfully

**Requirements:**

- Caller must be authorized to govern
- Ratio must be within allowed range

### setPriceSheetsActivated

```vyper
@external
def setPriceSheetsActivated(_isActivated: bool) -> bool:
```

Activates or deactivates the price sheets contract.

**Parameters:**

- `_isActivated`: True to activate, False to deactivate

**Returns:**

- True if activation state was changed successfully

**Requirements:**

- Caller must be authorized to govern
- New state must be different from current state
