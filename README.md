# ⟠ ethOracle

**Ethereum Intelligence MCP Server** — 10 tools | Part of [ToolOracle](https://tooloracle.io)

![Tools](https://img.shields.io/badge/MCP_Tools-10-10B898?style=flat-square)
![Status](https://img.shields.io/badge/Status-Live-00C853?style=flat-square)
![Chain](https://img.shields.io/badge/Chain-Ethereum-627EEA?style=flat-square)
![Tier](https://img.shields.io/badge/Tier-Free-2196F3?style=flat-square)

Token risk, ERC-20/721/1155/4626 analysis, contract verification, gas intelligence, protocol TVL, RWA/tokenization, stablecoin checks, yield vault analysis. Evidence-grade data for tokenized finance, compliance, and institutional DeFi.

## Quick Connect

```bash
# Claude Desktop / Cursor / Windsurf
npx -y mcp-remote https://feedoracle.io/mcp/ethoracle/
```

```json
{
  "mcpServers": {
    "ethoracle": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://feedoracle.io/mcp/ethoracle/"]
    }
  }
}
```

## Tools (10)

| Tool | Description |
|------|-------------|
| `eth_overview` | Ethereum ecosystem overview: ETH price, gas fees, TVL, block stats |
| `eth_token_risk` | ERC-20 token risk assessment: holder concentration, contract age, liquidity |
| `eth_contract_verify` | Verify smart contract: source code, ABI, compiler, proxy detection |
| `eth_gas` | Real-time gas oracle with USD cost estimates for transfers, ERC-20, Uniswap swaps |
| `eth_protocol_tvl` | DeFi protocol TVL intelligence. Empty = top-20 Ethereum protocols |
| `eth_erc4626_vaults` | ERC-4626 tokenized vault analysis: yield, TVL, risk scoring |
| `eth_rwa_tokenization` | RWA intelligence: tokenized bonds, treasuries, credit (Ondo, Maple, Centrifuge...) |
| `eth_stablecoin_check` | Stablecoin peg health: USDC, USDT, DAI, FRAX, PYUSD, RLUSD |
| `eth_wallet_intel` | Wallet intelligence: ETH balance, token holdings, recent transactions |
| `eth_defi_yields` | Top DeFi yield opportunities filtered by TVL and APY range |

## Use Cases

- **Compliance agents**: Contract verification, token risk scoring for MiCA/DORA
- **RWA monitoring**: Track tokenized treasuries, bonds, credit protocols on Ethereum
- **DeFi intelligence**: TVL, yields, vault analysis for institutional AI agents
- **Gas optimization**: Real-time cost estimates for agent transaction planning

## Pricing

| Tier | Rate Limit | Price |
|------|-----------|-------|
| Free | 100 calls/day | €0 |
| Pro | 10,000 calls/day | €29/month |
| Enterprise | Unlimited | Custom |

## Part of FeedOracle / ToolOracle

ethOracle is part of the **[FeedOracle](https://feedoracle.io)** evidence-grade compliance infrastructure and the **[ToolOracle](https://tooloracle.io)** ecosystem — production-ready MCP tools for AI agents.

**Blockchain Oracle Suite:**
- [ethOracle](https://github.com/tooloracle/ethoracle) — Ethereum (this repo)
- [xlmOracle](https://github.com/tooloracle/xlmoracle) — Stellar / XLM
- [xrplOracle](https://github.com/tooloracle/xrploracle) — XRP Ledger / RLUSD
- [bnbOracle](https://github.com/tooloracle/bnboracle) — BNB Chain
- [aptOracle](https://github.com/tooloracle/aptoracle) — Aptos / Move VM
- [baseOracle](https://github.com/tooloracle/baseoracle) — Base L2 (Coinbase)

## Links

- 🌐 Live: `https://feedoracle.io/mcp/ethoracle/`
- 📚 Docs: [feedoracle.io/docs](https://feedoracle.io/docs)
- 🏠 Platform: [feedoracle.io](https://feedoracle.io)

---

*Built by [FeedOracle](https://feedoracle.io) — Evidence by Design*
