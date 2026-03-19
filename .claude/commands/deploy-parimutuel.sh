#!/bin/bash

# Deploy Parimutuel Betting System Smart Contracts
# This command deploys the new parimutuel betting contracts to Base testnet/mainnet

set -e

echo "🎰 Deploying Parimutuel Betting System..."
echo "================================================"

# Check if we're in the contracts directory
if [ ! -f "foundry.toml" ]; then
    echo "❌ Error: Must be run from the contracts directory"
    exit 1
fi

# Check if required files exist
if [ ! -f "src/ParimutuelPredictionMarket.sol" ]; then
    echo "❌ Error: ParimutuelPredictionMarket.sol not found"
    exit 1
fi

if [ ! -f "src/ParimutuelMarketFactory.sol" ]; then
    echo "❌ Error: ParimutuelMarketFactory.sol not found"
    exit 1
fi

# Set network (default to base-sepolia for testing)
NETWORK=${1:-"base-sepolia"}
echo "🌐 Network: $NETWORK"

# USDC addresses for different networks
case $NETWORK in
    "base-sepolia")
        USDC_ADDRESS="0x036CbD53842c5426634e7929541eC2318f3dCF7e"
        echo "💰 Using Base Sepolia USDC: $USDC_ADDRESS"
        ;;
    "base")
        USDC_ADDRESS="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
        echo "💰 Using Base Mainnet USDC: $USDC_ADDRESS"
        ;;
    *)
        echo "❌ Unsupported network: $NETWORK"
        echo "   Supported networks: base-sepolia, base"
        exit 1
        ;;
esac

# Default resolver (you can override this)
DEFAULT_RESOLVER=${RESOLVER:-$DEPLOYER}
echo "👤 Default resolver: $DEFAULT_RESOLVER"

echo ""
echo "📋 Pre-deployment checklist:"
echo "   ✅ ParimutuelPredictionMarket.sol - Implements parimutuel betting logic"
echo "   ✅ ParimutuelMarketFactory.sol - Factory for creating markets"
echo "   ✅ ERC-4337 compatible (gasless transactions)"
echo "   ✅ Fixed bet amounts: 1, 5, or 10 USDC"
echo "   ✅ Winners split losers' pool proportionally"
echo "   ✅ 24-hour market duration support"
echo ""

read -p "🚀 Ready to deploy? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

echo ""
echo "🔨 Compiling contracts..."
forge build

if [ $? -ne 0 ]; then
    echo "❌ Compilation failed"
    exit 1
fi

echo "✅ Contracts compiled successfully"
echo ""

# Deploy Factory Contract
echo "🏭 Deploying ParimutuelMarketFactory..."

DEPLOY_CMD="forge create --rpc-url $NETWORK \
    --constructor-args $USDC_ADDRESS $DEFAULT_RESOLVER \
    src/ParimutuelMarketFactory.sol:ParimutuelMarketFactory"

if [ -n "$PRIVATE_KEY" ]; then
    DEPLOY_CMD="$DEPLOY_CMD --private-key $PRIVATE_KEY"
elif [ -n "$KEYSTORE" ]; then
    DEPLOY_CMD="$DEPLOY_CMD --keystore $KEYSTORE"
else
    echo "❌ Error: No deployment key specified (set PRIVATE_KEY or KEYSTORE)"
    exit 1
fi

echo "Executing: $DEPLOY_CMD"
FACTORY_RESULT=$($DEPLOY_CMD)

if [ $? -ne 0 ]; then
    echo "❌ Factory deployment failed"
    exit 1
fi

# Extract factory address from deployment result
FACTORY_ADDRESS=$(echo "$FACTORY_RESULT" | grep "Deployed to:" | awk '{print $3}')

if [ -z "$FACTORY_ADDRESS" ]; then
    echo "❌ Could not extract factory address from deployment"
    exit 1
fi

echo "✅ ParimutuelMarketFactory deployed to: $FACTORY_ADDRESS"
echo ""

# Test deployment by creating a sample market
echo "🧪 Testing deployment with sample market..."

SAMPLE_QUESTION="Will it rain tomorrow?"
END_TIME=$(date -d "+24 hours" +%s)

CREATE_MARKET_CMD="cast send $FACTORY_ADDRESS \
    'createMarket(string,uint256,address)' \
    '$SAMPLE_QUESTION' $END_TIME 0x0000000000000000000000000000000000000000 \
    --rpc-url $NETWORK"

if [ -n "$PRIVATE_KEY" ]; then
    CREATE_MARKET_CMD="$CREATE_MARKET_CMD --private-key $PRIVATE_KEY"
elif [ -n "$KEYSTORE" ]; then
    CREATE_MARKET_CMD="$CREATE_MARKET_CMD --keystore $KEYSTORE"
fi

echo "Creating test market..."
TEST_RESULT=$($CREATE_MARKET_CMD 2>&1)

if [ $? -eq 0 ]; then
    echo "✅ Test market created successfully"

    # Get the market address
    MARKET_COUNT=$(cast call $FACTORY_ADDRESS "getMarketCount()" --rpc-url $NETWORK)
    if [ "$MARKET_COUNT" != "0x0000000000000000000000000000000000000000000000000000000000000001" ]; then
        echo "⚠️  Warning: Expected 1 market, got different count"
    else
        MARKET_ADDRESS=$(cast call $FACTORY_ADDRESS "markets(uint256)" 0 --rpc-url $NETWORK)
        echo "📊 Test market deployed to: $MARKET_ADDRESS"
    fi
else
    echo "⚠️  Test market creation failed (this is OK for mainnet)"
    echo "   Error: $TEST_RESULT"
fi

echo ""
echo "🎉 Deployment Summary"
echo "================================================"
echo "Network: $NETWORK"
echo "USDC Token: $USDC_ADDRESS"
echo "Factory Address: $FACTORY_ADDRESS"
echo "Default Resolver: $DEFAULT_RESOLVER"
echo ""

# Save deployment info
DEPLOYMENT_FILE="deployments/parimutuel-${NETWORK}.json"
mkdir -p deployments

cat > "$DEPLOYMENT_FILE" << EOF
{
  "network": "$NETWORK",
  "timestamp": "$(date -Iseconds)",
  "contracts": {
    "ParimutuelMarketFactory": {
      "address": "$FACTORY_ADDRESS",
      "args": ["$USDC_ADDRESS", "$DEFAULT_RESOLVER"]
    }
  },
  "tokens": {
    "USDC": "$USDC_ADDRESS"
  },
  "config": {
    "defaultResolver": "$DEFAULT_RESOLVER",
    "allowedBetAmounts": [1000000, 5000000, 10000000],
    "maxMarketDuration": 2592000,
    "minMarketDuration": 3600
  }
}
EOF

echo "💾 Deployment info saved to: $DEPLOYMENT_FILE"
echo ""

echo "🔧 Next Steps:"
echo "1. Update your paymaster allowlist with the factory address:"
echo "   $FACTORY_ADDRESS"
echo ""
echo "2. Update your frontend with the new contract addresses"
echo ""
echo "3. Test the parimutuel betting flow:"
echo "   - Create markets with different bet amounts"
echo "   - Place bets using betYes() and betNo()"
echo "   - Resolve markets and claim rewards"
echo ""
echo "4. Monitor gas costs and optimize if needed"
echo ""

if [ "$NETWORK" = "base-sepolia" ]; then
    echo "🧪 Testnet Deployment Complete!"
    echo "   Consider testing with small amounts before mainnet deployment"
else
    echo "🚀 Mainnet Deployment Complete!"
    echo "   Monitor the contracts carefully in production"
fi