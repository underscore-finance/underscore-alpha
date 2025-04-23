import pytest
import boa

from conf_utils import filter_logs
from constants import ZERO_ADDRESS, EIGHTEEN_DECIMALS, MAX_UINT256, DEPOSIT_UINT256, WITHDRAWAL_UINT256, REBALANCE_UINT256, TRANSFER_UINT256, CONVERSION_UINT256
from utils.BluePrint import CORE_TOKENS


#########
# Tests #
#########


def test_batch_actions_simple(special_ai_wallet, special_agent, createActionInstruction, mock_lego_alpha, alpha_token, alpha_token_whale, alpha_token_erc4626_vault):
    lego_id = mock_lego_alpha.legoId()
    amount = 1_000 * EIGHTEEN_DECIMALS
    alpha_token.transfer(special_ai_wallet, amount, sender=alpha_token_whale)

    # create instructions
    instructions = [
        createActionInstruction(DEPOSIT_UINT256, lego_id, alpha_token.address, alpha_token_erc4626_vault.address, amount),
        createActionInstruction(WITHDRAWAL_UINT256, lego_id, alpha_token.address, alpha_token_erc4626_vault.address, amount),
    ]

    special_agent.performBatchActions(special_ai_wallet, instructions, sender=special_agent.owner())

    log1 = filter_logs(special_agent, "UserWalletDeposit")[0]
    log2 = filter_logs(special_agent, "UserWalletWithdrawal")[0]

    assert log1.signer == special_agent.address
    assert log1.isSignerAgent

    assert log2.signer == special_agent.address
    assert log2.isSignerAgent


@pytest.base
def test_batch_action_withdraw_swap(special_ai_wallet, special_agent, owner, lego_aave_v3, createActionInstruction, oracle_chainlink, getTokenAndWhale, governor, lego_uniswap_v2, lego_uniswap_v3, fork, createSwapActionInstruction):

    # usdc setup
    usdc, usdc_whale = getTokenAndWhale("usdc")
    usdc_amount = 10_000 * (10 ** usdc.decimals())
    usdc.transfer(special_ai_wallet, usdc_amount, sender=usdc_whale)
    assert oracle_chainlink.setChainlinkFeed(usdc, "0x7e860098F58bBFC8648a4311b374B1D669a2bc6B", sender=governor)

    # deposit usdc into aave v3
    aave_usdc = boa.from_etherscan("0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB")
    if lego_aave_v3.vaultToAsset(aave_usdc) == ZERO_ADDRESS:
        lego_aave_v3.addAssetOpportunity(usdc.address, sender=governor)
    special_ai_wallet.depositTokens(lego_aave_v3.legoId(), usdc.address, aave_usdc, usdc_amount, sender=owner)

    # weth setup
    weth = boa.from_etherscan(CORE_TOKENS[fork]["WETH"], name="weth token")
    univ2_weth_usdc_pool = "0x88A43bbDF9D098eEC7bCEda4e2494615dfD9bB9C"

    # virtual setup
    virtual = boa.from_etherscan(CORE_TOKENS[fork]["VIRTUAL"], name="virtual token")
    univ2_weth_virtual_pool = "0xE31c372a7Af875b3B5E0F3713B17ef51556da667"
    univ3_weth_virtual_pool = "0x9c087Eb773291e50CF6c6a90ef0F4500e349B903"

    # cbbtc setup
    cbbtc = boa.from_etherscan(CORE_TOKENS[fork]["CBBTC"], name="cbbtc token")
    weth_cbbtc_pool = "0x8c7080564B5A792A33Ef2FD473fbA6364d5495e5"

    # usdc -> weth -> virtual
    first_instruction = (
        lego_uniswap_v2.legoId(),
        usdc_amount,
        0,
        [usdc, weth, virtual],
        [univ2_weth_usdc_pool, univ2_weth_virtual_pool]
    )

    # virtual -> weth -> cbbtc
    second_instruction = (
        lego_uniswap_v3.legoId(),
        MAX_UINT256,
        0,
        [virtual, weth, cbbtc],
        [univ3_weth_virtual_pool, weth_cbbtc_pool]
    )

    # create instructions
    instructions = [
        createActionInstruction(WITHDRAWAL_UINT256, lego_aave_v3.legoId(), usdc.address, aave_usdc, usdc_amount),
        createSwapActionInstruction([first_instruction, second_instruction]),
    ]

    special_agent.performBatchActions(special_ai_wallet, instructions, sender=special_agent.owner())

    log1 = filter_logs(special_agent, "UserWalletWithdrawal")[0]
    log2 = filter_logs(special_agent, "UserWalletSwap")[0]

    assert log1.signer == special_agent.address
    assert log1.isSignerAgent

    assert log2.signer == special_agent.address
    assert log2.isSignerAgent

    assert cbbtc.balanceOf(special_ai_wallet) != 0
    assert usdc.balanceOf(special_ai_wallet) == 0
    assert aave_usdc.balanceOf(special_ai_wallet) == 0


# def test_batch_actions(ai_wallet, ai_wallet_config, owner, agent, mock_lego_alpha, alpha_token, mock_lego_alpha_another, alpha_token_erc4626_vault, alpha_token_erc4626_vault_another, alpha_token_whale, sally):
#     lego_id = mock_lego_alpha.legoId()
#     alt_lego_id = mock_lego_alpha_another.legoId()
#     amount = 1_000 * EIGHTEEN_DECIMALS

#     # Setup agent permissions
#     ai_wallet_config.addAssetForAgent(agent, alpha_token, sender=owner)
#     ai_wallet_config.addLegoIdForAgent(agent, lego_id, sender=owner)
#     ai_wallet_config.addLegoIdForAgent(agent, alt_lego_id, sender=owner)
#     ai_wallet_config.setWhitelistAddr(sally, True, sender=owner)

#     # Transfer tokens to wallet
#     alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)

#     # Create batch instructions
#     instructions = [
#         # Deposit
#         (DEPOSIT_UINT256, lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256,
#          ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),  # ActionType.DEPOSIT = 0
#         # Withdrawal
#         (WITHDRAWAL_UINT256, lego_id, alpha_token, alpha_token_erc4626_vault, amount // 2,
#          ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),  # ActionType.WITHDRAWAL = 1
#         # Rebalance
#         (REBALANCE_UINT256, lego_id, alpha_token, alpha_token_erc4626_vault, MAX_UINT256, ZERO_ADDRESS,
#          alt_lego_id, alpha_token_erc4626_vault_another, ZERO_ADDRESS, 0, ZERO_ADDRESS),  # ActionType.REBALANCE = 2
#         # Transfer
#         (TRANSFER_UINT256, 0, alpha_token, ZERO_ADDRESS, MAX_UINT256, sally, 0,
#          ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),  # ActionType.TRANSFER = 3
#     ]

#     # Test batch actions by owner
#     assert ai_wallet.performManyActions(instructions, sender=agent)

#     # deposit
#     log = filter_logs(ai_wallet, "UserWalletDeposit")[0]
#     assert log.signer == agent
#     assert log.asset == alpha_token.address
#     assert log.vaultToken == alpha_token_erc4626_vault.address
#     assert log.assetAmountDeposited == amount
#     assert log.vaultTokenAmountReceived == amount
#     assert log.refundAssetAmount == 0
#     assert log.legoId == lego_id
#     assert log.legoAddr == mock_lego_alpha.address
#     assert log.isSignerAgent

#     # withdrawal
#     log = filter_logs(ai_wallet, "UserWalletWithdrawal")[0]
#     assert log.signer == agent
#     assert log.asset == alpha_token.address
#     assert log.vaultToken == alpha_token_erc4626_vault.address
#     assert log.assetAmountReceived == amount // 2
#     assert log.vaultTokenAmountBurned == amount // 2
#     assert log.refundVaultTokenAmount == 0
#     assert log.legoId == lego_id
#     assert log.legoAddr == mock_lego_alpha.address
#     assert log.isSignerAgent

#     # rebalance
#     log = filter_logs(ai_wallet, "UserWalletWithdrawal")[1]
#     assert log.signer == agent
#     assert log.asset == alpha_token.address
#     assert log.vaultToken == alpha_token_erc4626_vault.address
#     assert log.assetAmountReceived == amount // 2
#     assert log.vaultTokenAmountBurned == amount // 2
#     assert log.refundVaultTokenAmount == 0
#     assert log.legoId == lego_id
#     assert log.legoAddr == mock_lego_alpha.address
#     assert log.isSignerAgent

#     log = filter_logs(ai_wallet, "UserWalletDeposit")[1]
#     assert log.signer == agent
#     assert log.asset == alpha_token.address
#     assert log.vaultToken == alpha_token_erc4626_vault_another.address
#     assert log.assetAmountDeposited == amount // 2
#     assert log.vaultTokenAmountReceived == amount // 2
#     assert log.refundAssetAmount == 0
#     assert log.legoId == alt_lego_id
#     assert log.legoAddr == mock_lego_alpha_another.address
#     assert log.isSignerAgent

#     # transfer
#     log = filter_logs(ai_wallet, "UserWalletFundsTransferred")[0]
#     assert log.recipient == sally
#     assert log.asset == alpha_token.address
#     assert log.amount == amount // 2
#     assert log.isSignerAgent

#     # data
#     assert alpha_token.balanceOf(ai_wallet) == 0
#     assert alpha_token.balanceOf(sally) == amount // 2

#     assert alpha_token_erc4626_vault.balanceOf(ai_wallet) == 0
#     assert alpha_token_erc4626_vault_another.balanceOf(ai_wallet) == amount // 2


# @pytest.base
# def test_batch_actions_deposit_usdc_in_many_legos(ai_wallet, agent, getTokenAndWhale, lego_morpho, lego_fluid, governor):
#     usdc, usdc_whale = getTokenAndWhale("usdc")
#     amount = 10_000_000
#     usdc.transfer(ai_wallet, amount, sender=usdc_whale)
#     assert usdc.balanceOf(ai_wallet) == amount

#     # Morpho
#     morpho_vault_token = boa.from_etherscan("0xc1256ae5ff1cf2719d4937adb3bbccab2e00a2ca", name="morpho_vault_token")
#     assert lego_morpho.addAssetOpportunity(usdc.address, morpho_vault_token, sender=governor)
#     assert morpho_vault_token.balanceOf(ai_wallet) == 0

#     # Fluid
#     fluid_vault_token = boa.from_etherscan("0xf42f5795D9ac7e9D757dB633D693cD548Cfd9169", name="fluid_vault_token")
#     assert lego_fluid.addAssetOpportunity(usdc.address, fluid_vault_token, sender=governor)
#     assert fluid_vault_token.balanceOf(ai_wallet) == 0

#     # Create batch instructions
#     instructions = [
#         (
#             DEPOSIT_UINT256,
#             lego_morpho.legoId(),
#             usdc.address,
#             morpho_vault_token.address,
#             2_000_000,
#             ZERO_ADDRESS,
#             0,
#             ZERO_ADDRESS,
#             ZERO_ADDRESS,
#             0,
#             ZERO_ADDRESS,
#         ),
#         (
#             DEPOSIT_UINT256,
#             lego_fluid.legoId(),
#             usdc.address,
#             fluid_vault_token.address,
#             2_000_000,
#             ZERO_ADDRESS,
#             0,
#             ZERO_ADDRESS,
#             ZERO_ADDRESS,
#             0,
#             ZERO_ADDRESS,
#         ),
#     ]

#     # Test batch actions by owner
#     assert ai_wallet.performManyActions(instructions, sender=agent)
#     assert usdc.balanceOf(ai_wallet) != amount

#     assert morpho_vault_token.balanceOf(ai_wallet) != 0
#     assert fluid_vault_token.balanceOf(ai_wallet) != 0



# def test_allowed_actions_batch_operations(ai_wallet, ai_wallet_config, owner, agent, mock_lego_alpha, alpha_token, alpha_token_erc4626_vault, alpha_token_whale, sally):
#     # Setup initial permissions
#     ai_wallet_config.addAssetForAgent(agent, alpha_token, sender=owner)
#     ai_wallet_config.addLegoIdForAgent(agent, mock_lego_alpha.legoId(), sender=owner)
#     ai_wallet_config.setWhitelistAddr(sally, True, sender=owner)

#     # Set restricted permissions - only allow deposits, transfers, add liquidity, claim rewards, and borrow
#     allowed_actions = (True, True, False, False, True, False, False, True, False, True, True, False)
#     ai_wallet_config.modifyAllowedActions(agent, allowed_actions, sender=owner)

#     # Transfer tokens to wallet
#     amount = 1_000 * EIGHTEEN_DECIMALS
#     alpha_token.transfer(ai_wallet, amount, sender=alpha_token_whale)

#     # Create batch instructions with mix of allowed and disallowed actions
#     instructions = [
#         # Deposit (allowed)
#         (DEPOSIT_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, MAX_UINT256, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),
#         # Withdrawal (not allowed)
#         (WITHDRAWAL_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, amount // 2, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),
#         # Add Liquidity (allowed)
#         (ADD_LIQ_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, amount // 4, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),
#         # Remove Liquidity (not allowed)
#         (REMOVE_LIQ_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, amount // 4, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),
#         # Claim Rewards (allowed)
#         (CLAIM_REWARDS_UINT256, mock_lego_alpha.legoId(), ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),
#         # Borrow (allowed)
#         (BORROW_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, amount // 4, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),
#         # Repay (not allowed)
#         (REPAY_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, amount // 4, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),
#     ]

#     # Test batch operations fail if any action is not allowed
#     with boa.reverts("agent not allowed"):
#         ai_wallet.performManyActions(instructions, sender=agent)

#     # Test batch operations with only allowed actions
#     allowed_instructions = [
#         # Deposit (allowed)
#         (DEPOSIT_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, amount // 3, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),
#         # Transfer (allowed)
#         (TRANSFER_UINT256, 0, alpha_token, ZERO_ADDRESS, amount // 3, sally, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),
#         # Add Liquidity (allowed)
#         (ADD_LIQ_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, amount // 3, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),
#         # Claim Rewards (allowed)
#         (CLAIM_REWARDS_UINT256, mock_lego_alpha.legoId(), ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),
#         # Borrow (allowed)
#         (BORROW_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, amount // 3, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),
#     ]

#     assert ai_wallet.performManyActions(allowed_instructions, sender=agent) 



# def test_batch_transaction_fees(new_ai_wallet, alpha_token, alpha_token_whale, mock_lego_alpha, alpha_token_erc4626_vault, governor, price_sheets, bob_agent):
#     """Test transaction fees in batch operations"""
#     # Enable both protocol and bob_agent fees
#     assert price_sheets.removeAgentSubPrice(bob_agent, sender=governor)
#     assert price_sheets.removeProtocolSubPrice(sender=governor)

#     # Fund wallet
#     alpha_token.transfer(new_ai_wallet, 1000 * EIGHTEEN_DECIMALS, sender=alpha_token_whale)

#     pre_protocol_wallet = alpha_token.balanceOf(governor)
#     pre_agent_wallet = alpha_token.balanceOf(bob_agent)

#     # Create batch instructions
#     instructions = [
#         # Deposit instruction
#         (DEPOSIT_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 100 * EIGHTEEN_DECIMALS, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS),
#         # Withdrawal instruction
#         (WITHDRAWAL_UINT256, mock_lego_alpha.legoId(), alpha_token, alpha_token_erc4626_vault, 50 * EIGHTEEN_DECIMALS, ZERO_ADDRESS, 0, ZERO_ADDRESS, ZERO_ADDRESS, 0, ZERO_ADDRESS)
#     ]

#     # Execute batch
#     assert new_ai_wallet.performManyActions(instructions, sender=bob_agent)

#     # Verify batch fees
#     logs = filter_logs(new_ai_wallet, "UserWalletTransactionFeePaid")

#     # Protocol fees: (0.50% of 100) + (1.00% of 50) = 1 alpha
#     assert logs[0].asset == alpha_token.address
#     assert logs[0].amount == 1 * EIGHTEEN_DECIMALS
#     assert logs[0].usdValue == 1 * EIGHTEEN_DECIMALS
#     assert not logs[0].isAgent

#     # Agent fees: (1.00% of 100) + (2.00% of 50) = 2 alpha
#     assert logs[1].asset == alpha_token.address
#     assert logs[1].amount == 2 * EIGHTEEN_DECIMALS
#     assert logs[1].usdValue == 2 * EIGHTEEN_DECIMALS
#     assert logs[1].isAgent

#     assert alpha_token.balanceOf(governor) == pre_protocol_wallet + logs[0].amount
#     assert alpha_token.balanceOf(bob_agent) == pre_agent_wallet + logs[1].amount
