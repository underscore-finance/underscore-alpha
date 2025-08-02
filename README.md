# Underscore Alpha Codebase

> **Note: This is the Underscore Alpha codebase and is outdated.**
>
> For the current implementation, please visit:
>
> - **Current Protocol**: https://github.com/underscore-finance/underscore-protocol
> - **Documentation**: https://docs.underscore.finance/
> - **Homepage**: https://underscore.finance/

---

## License

Underscore Protocol uses a dual-licensing approach:

- **Core Protocol (BUSL-1.1)**: The core protocol implementation and DeFi integrations (legos) are licensed under the [Business Source License 1.1](LICENSE) (BUSL-1.1). This allows for non-production use and will automatically convert to the MIT License on March 6, 2029, or earlier as specified at [LICENSE_DATE.md](LICENSE_DATE.md).

- **Interfaces (MIT)**: All interfaces and integration libraries are licensed under the MIT License to enable seamless integration with the protocol.

For production use of BUSL-1.1 licensed code, please refer to the [Additional Use Grants](LICENSE_GRANTS.md) or contact Hightop Financial, Inc. for a commercial license.

For detailed information about which directories and files are covered by each license, please see [LICENSE_INFO.md](LICENSE_INFO.md).

## Deployment Addresses

### Base Mainnet

| Core Contracts           |                                                                                                                       |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| AddyRegistry             | [0x7BcD6d471D1A068012A79347C7a944d1Df01a1AE](https://basescan.org/address/0x7BcD6d471D1A068012A79347C7a944d1Df01a1AE) |
| AgentFactory             | [0x7C4be37a65E8410c0fb03d62059E3cB04f78c565](https://basescan.org/address/0x7C4be37a65E8410c0fb03d62059E3cB04f78c565) |
| UserWalletTemplate       | [0xe43D5bD11a2A6A9348EFC516ad9Ac3D32164A5A0](https://basescan.org/address/0xe43D5bD11a2A6A9348EFC516ad9Ac3D32164A5A0) |
| UserWalletConfigTemplate | [0x61293F1bF484d20dcc841175b4E4A0F46c26658c](https://basescan.org/address/0x61293F1bF484d20dcc841175b4E4A0F46c26658c) |
| AgentTemplate            | [0x76Eb19Ae42c07a7AD50aFD58b579a7c45bd70183](https://basescan.org/address/0x76Eb19Ae42c07a7AD50aFD58b579a7c45bd70183) |
| LegoRegistry             | [0x8D8593FE154d14976352FA2CE30322EcDF99C72a](https://basescan.org/address/0x8D8593FE154d14976352FA2CE30322EcDF99C72a) |
| OracleRegistry           | [0xe133F22aAdC23F9B7ca7A9f16B6D9A0C662Cf90b](https://basescan.org/address/0xe133F22aAdC23F9B7ca7A9f16B6D9A0C662Cf90b) |
| PriceSheets              | [0xD15331Cf355B5D8EF017c1FD49516b95593FA6aA](https://basescan.org/address/0xD15331Cf355B5D8EF017c1FD49516b95593FA6aA) |
| LegoHelper               | [0xF80b87DD1096f9E68739f55B9807Df1CB21422E3](https://basescan.org/address/0xF80b87DD1096f9E68739f55B9807Df1CB21422E3) |

| Oracles        |                                                                                                                       |
| -------------- | --------------------------------------------------------------------------------------------------------------------- |
| ChainlinkFeeds | [0x605c6ab843d65dD14b00CEB33f445D7f9bbb7930](https://basescan.org/address/0x605c6ab843d65dD14b00CEB33f445D7f9bbb7930) |
| PythFeeds      | [0x415a2fe1e591619c6c12Df09eAEc8a598224F9fE](https://basescan.org/address/0x415a2fe1e591619c6c12Df09eAEc8a598224F9fE) |
| StorkFeeds     | [0xD47D74C56c17Bf3B7236e8a7eb97D3194c3d477c](https://basescan.org/address/0xD47D74C56c17Bf3B7236e8a7eb97D3194c3d477c) |

| Yield Legos    |                                                                                                                       |
| -------------- | --------------------------------------------------------------------------------------------------------------------- |
| LegoAaveV3     | [0x8c94cfC11A9340e45032e5021881cc312993Bf15](https://basescan.org/address/0x8c94cfC11A9340e45032e5021881cc312993Bf15) |
| LegoCompoundV3 | [0xF86d1D68C951d163aBc383C508740df6ddED500C](https://basescan.org/address/0xF86d1D68C951d163aBc383C508740df6ddED500C) |
| LegoEuler      | [0xB2a1cdC1D896eE37cD432b591FeC2664294286FB](https://basescan.org/address/0xB2a1cdC1D896eE37cD432b591FeC2664294286FB) |
| LegoFluid      | [0xc4a864F5543D3CDB06D5F3419c18315f2cDe9675](https://basescan.org/address/0xc4a864F5543D3CDB06D5F3419c18315f2cDe9675) |
| LegoMoonwell   | [0x3890573c04A13d1D982104c7DaDb17F66cb1aE6c](https://basescan.org/address/0x3890573c04A13d1D982104c7DaDb17F66cb1aE6c) |
| LegoMorpho     | [0x825309418B066603C2732fdA08d39A79CAA5CC8e](https://basescan.org/address/0x825309418B066603C2732fdA08d39A79CAA5CC8e) |
| LegoSky        | [0x3514536163D5c0c5207A6A1230fc76bEe8CE8506](https://basescan.org/address/0x3514536163D5c0c5207A6A1230fc76bEe8CE8506) |

| Dex Legos          |                                                                                                                       |
| ------------------ | --------------------------------------------------------------------------------------------------------------------- |
| LegoAeroClassic    | [0x61C8D98F01B066fA99eb2cf2E6069a7e5d891313](https://basescan.org/address/0x61C8D98F01B066fA99eb2cf2E6069a7e5d891313) |
| LegoAeroSlipstream | [0x0891DdE2eC48f9663A1c9a81820c283dD8846594](https://basescan.org/address/0x0891DdE2eC48f9663A1c9a81820c283dD8846594) |
| LegoCurve          | [0x6118D44763a556Cf8d113ebBce853E14a0C67997](https://basescan.org/address/0x6118D44763a556Cf8d113ebBce853E14a0C67997) |
| LegoUniswapV2      | [0x9973e271Bd6cAb8Ce1CAEaBAB8a1bEbcB6EdD535](https://basescan.org/address/0x9973e271Bd6cAb8Ce1CAEaBAB8a1bEbcB6EdD535) |
| LegoUniswapV3      | [0x6bfd82031a968685358DA84ebB797c3C068EC704](https://basescan.org/address/0x6bfd82031a968685358DA84ebB797c3C068EC704) |
