# Underscore Protocol License Information

## Overview

Underscore Protocol is licensed under the Business Source License 1.1 (BUSL-1.1). This license was chosen to balance the benefits of open source with protection for the Underscore community and ecosystem.

## License Structure

The Underscore Protocol codebase is licensed under two licenses:

1. **Business Source License 1.1 (BUSL-1.1)**: This applies to the core protocol contracts and implementation details.
2. **MIT License**: This applies to interfaces and peripheral contracts needed for integration.

## Directory-Specific Licensing

### BUSL-1.1 Licensed Directories and Files

The following directories and their contents are licensed under the Business Source License 1.1:

- `contracts/core/` - Core protocol implementation
- `contracts/legos/` - All DeFi protocol integrations (Uniswap, Aave, etc.)
- `contracts/modules/` - Supporting modules for the core protocol
- `contracts/oracles/` - Price oracle implementations

### MIT Licensed Directories and Files

The following directories and their contents are licensed under the MIT License:

- `interfaces/` - All interface definitions
- `contracts/mock/` - mock contracts for testing
- `utils/` - Helper utilities needed for integration

## What the BUSL-1.1 Means for You

The BUSL-1.1 license:

- Allows you to view, modify, and use the code for non-production purposes (development, testing, academic research, personal learning)
- Restricts production use unless:
  - You receive an Additional Use Grant
  - The Change Date is reached (March 6, 2029, or earlier if specified at https://github.com/underscore-finance/underscore/blob/main/LICENSE_DATE.md)
- Will automatically convert to the MIT License on the Change Date

## What You Can Do Without Additional Permission

- View and study all code
- Fork the repository
- Modify the code for non-production use
- Use the code for development and testing
- Contribute to the codebase
- Integrate with the protocol through the MIT-licensed interfaces

## What Requires Additional Permission

Production use of BUSL-1.1 licensed code requires one of the following:

1. **Additional Use Grant**: Specific permission for production use, which can be granted through the governance process
2. **Commercial License**: A separate license agreement with Hightop Financial, Inc.
3. **Wait for the Change Date**: After March 6, 2029 (or an earlier date if specified), the code will be available under the MIT License

## Obtaining an Additional Use Grant

Additional Use Grants may be issued through the Underscore governance process. These grants are recorded at https://github.com/underscore-finance/underscore/blob/main/LICENSE_GRANTS.md.

To request an Additional Use Grant, check the above file.

## MIT-Licensed Components

The following components are licensed under the MIT License to enable integration with the protocol:

- Interface definitions (all files in `interfaces/` directory)
- Mock smart contracts used for testing (all files in `contracts/mock/` directory)
- Helper utilities (in the `utils/` directory)

## License Verification

To verify which license applies to a specific file:

1. Check the directory-specific licensing section in this document
2. If the file is in a directory listed under MIT Licensed Directories, it is MIT licensed
3. If the file is in a directory listed under BUSL-1.1 Licensed Directories, it is BUSL-1.1 licensed

## Questions and Commercial Licensing

For questions about the license or to inquire about commercial licensing options, please contact:
- Email: team@hightop.com

## Disclaimer

This document is provided for informational purposes only and does not constitute legal advice. You should consult with a lawyer to discuss your specific situation and licensing needs. 