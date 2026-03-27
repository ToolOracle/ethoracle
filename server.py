#!/usr/bin/env python3
"""ETHOracle MCP Server v1.0.0 — Port 11201
Ethereum Intelligence for AI Agents.
Token risk, ERC-20/721/1155/4626 analysis, contract verification,
gas intelligence, protocol TVL, RWA/tokenization, whale tracking,
stablecoin checks, yield vault analysis. Evidence-grade data for
tokenized finance, compliance, and institutional DeFi.
"""
import os, sys, json, logging, aiohttp, asyncio
from datetime import datetime, timezone

sys.path.insert(0, "/root/whitelabel")
from shared.utils.mcp_base import WhitelabelMCPServer

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [ETHOracle] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(),
              logging.FileHandler("/root/whitelabel/logs/ethoracle.log", mode="a")])
logger = logging.getLogger("ETHOracle")

PRODUCT_NAME  = "ETHOracle"
VERSION       = "1.0.0"
PORT_MCP      = 11201
PORT_HEALTH   = 11202

# APIs
ETHERSCAN  = "https://api.etherscan.io/v2/api"
LLAMA      = "https://api.llama.fi"
LLAMA_Y    = "https://yields.llama.fi"
CG         = "https://api.coingecko.com/api/v3"
ETH_RPC    = "https://ethereum.publicnode.com"
ETHERSCAN_KEY = os.getenv("ETHERSCAN_API_KEY", "")

HEADERS = {"User-Agent": "ETHOracle-ToolOracle/1.0", "Accept": "application/json"}

def ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

async def get(url, params=None, timeout=15):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, params=params, headers=HEADERS,
                             timeout=aiohttp.ClientTimeout(total=timeout)) as r:
                if r.status == 200:
                    return await r.json(content_type=None)
                return {"error": f"HTTP {r.status}"}
    except Exception as e:
        return {"error": str(e)}

async def eth_rpc(method, params=None):
    try:
        body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or []}
        async with aiohttp.ClientSession() as s:
            async with s.post(ETH_RPC, json=body,
                              headers={"Content-Type": "application/json"},
                              timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    d = await r.json(content_type=None)
                    return d.get("result")
    except:
        pass
    return None

async def etherscan(params, timeout=15):
    p = {"chainid": "1", "apikey": ETHERSCAN_KEY, **params}
    return await get(ETHERSCAN, p, timeout)

def risk_grade(score):
    if score >= 80: return "A"
    if score >= 60: return "B"
    if score >= 40: return "C"
    if score >= 20: return "D"
    return "F"

def wei_to_eth(wei_hex):
    try:
        return int(wei_hex, 16) / 1e18
    except:
        return 0

# ── Tool Handlers ─────────────────────────────────────────

async def handle_overview(args):
    """Ethereum ecosystem overview: price, gas, TVL, network stats"""
    eth_price, tvl_data, gas_data = await asyncio.gather(
        get(f"{CG}/simple/price", {"ids": "ethereum", "vs_currencies": "usd,eur",
            "include_24hr_change": "true", "include_market_cap": "true", "include_24hr_vol": "true"}),
        get(f"{LLAMA}/v2/chains"),
        etherscan({"module": "gastracker", "action": "gasoracle"}),
    )
    eth = eth_price.get("ethereum", {}) if isinstance(eth_price, dict) else {}
    eth_tvl = 0
    if isinstance(tvl_data, list):
        for c in tvl_data:
            if c.get("name") == "Ethereum":
                eth_tvl = c.get("tvl", 0)
                break
    gas = gas_data.get("result", {}) if isinstance(gas_data, dict) else {}

    # Get latest block
    block_hex = await eth_rpc("eth_blockNumber")
    block = int(block_hex, 16) if block_hex else 0

    return {
        "chain": "Ethereum",
        "network": "mainnet",
        "timestamp": ts(),
        "price": {"usd": eth.get("usd"), "eur": eth.get("eur"),
                  "change_24h": eth.get("usd_24h_change"),
                  "market_cap_usd": eth.get("usd_market_cap"),
                  "volume_24h_usd": eth.get("usd_24h_vol")},
        "network_stats": {"latest_block": block,
                          "total_tvl_usd": round(eth_tvl, 2)},
        "gas": {"safe_gwei": gas.get("SafeGasPrice"),
                "standard_gwei": gas.get("ProposeGasPrice"),
                "fast_gwei": gas.get("FastGasPrice"),
                "base_fee": gas.get("suggestBaseFee")},
        "source": "CoinGecko + DefiLlama + Etherscan"
    }

async def handle_token_risk(args):
    """ERC-20 token risk assessment: holder concentration, contract age, liquidity"""
    contract = args.get("contract_address", "").strip()
    if not contract:
        return {"error": "contract_address required"}

    info, holders, txcount, supply = await asyncio.gather(
        etherscan({"module": "token", "action": "tokeninfo", "contractaddress": contract}),
        etherscan({"module": "token", "action": "tokenholderlist",
                   "contractaddress": contract, "page": "1", "offset": "10"}),
        etherscan({"module": "account", "action": "tokentx",
                   "contractaddress": contract, "page": "1", "offset": "1", "sort": "desc"}),
        etherscan({"module": "stats", "action": "tokensupply", "contractaddress": contract}),
    )

    token_info = {}
    if isinstance(info, dict) and info.get("status") == "1":
        r = info.get("result", [{}])
        token_info = r[0] if isinstance(r, list) and r else {}

    top_holders = []
    if isinstance(holders, dict) and holders.get("status") == "1":
        for h in (holders.get("result") or [])[:5]:
            top_holders.append({
                "address": h.get("TokenHolderAddress"),
                "share_pct": round(float(h.get("TokenHolderQuantity", 0)) /
                                   max(float(supply.get("result", 1) or 1), 1) * 100, 4)
            })

    # Score
    score = 50
    top5_pct = sum(h["share_pct"] for h in top_holders)
    if top5_pct > 80: score -= 25
    elif top5_pct > 50: score -= 10
    name = token_info.get("tokenName", "Unknown")
    symbol = token_info.get("symbol", "?")
    divisor = token_info.get("divisor", "18")

    return {
        "contract": contract,
        "name": name,
        "symbol": symbol,
        "decimals": divisor,
        "total_supply": supply.get("result") if isinstance(supply, dict) else None,
        "risk_score": score,
        "risk_grade": risk_grade(score),
        "top_holders": top_holders,
        "top5_concentration_pct": round(top5_pct, 2),
        "concentration_risk": "HIGH" if top5_pct > 70 else "MEDIUM" if top5_pct > 40 else "LOW",
        "timestamp": ts(),
        "source": "Etherscan"
    }

async def handle_contract_verify(args):
    """Verify Ethereum smart contract: source code, ABI, compiler, audit status"""
    contract = args.get("contract_address", "").strip()
    if not contract:
        return {"error": "contract_address required"}

    source, abi = await asyncio.gather(
        etherscan({"module": "contract", "action": "getsourcecode",
                   "address": contract}),
        etherscan({"module": "contract", "action": "getabi",
                   "address": contract}),
    )

    src_result = {}
    is_verified = False
    if isinstance(source, dict) and source.get("status") == "1":
        r = source.get("result", [{}])
        src_result = r[0] if isinstance(r, list) and r else {}
        is_verified = bool(src_result.get("SourceCode"))

    abi_ok = isinstance(abi, dict) and abi.get("status") == "1" and abi.get("result") != "Contract source code not verified"

    score = 70 if is_verified else 20
    if abi_ok: score += 10

    return {
        "contract": contract,
        "verified": is_verified,
        "abi_available": abi_ok,
        "contract_name": src_result.get("ContractName"),
        "compiler": src_result.get("CompilerVersion"),
        "optimization": src_result.get("OptimizationUsed") == "1",
        "license": src_result.get("LicenseType"),
        "proxy": src_result.get("Proxy") == "1",
        "implementation": src_result.get("Implementation") or None,
        "risk_score": score,
        "risk_grade": risk_grade(score),
        "risk_note": "Unverified contracts carry significantly higher risk" if not is_verified else "Source code verified on Etherscan",
        "timestamp": ts(),
        "source": "Etherscan"
    }

async def handle_gas(args):
    """Real-time Ethereum gas oracle with USD cost estimates"""
    gas, eth_price = await asyncio.gather(
        etherscan({"module": "gastracker", "action": "gasoracle"}),
        get(f"{CG}/simple/price", {"ids": "ethereum", "vs_currencies": "usd"}),
    )
    g = gas.get("result", {}) if isinstance(gas, dict) else {}
    eth_usd = eth_price.get("ethereum", {}).get("usd", 0) if isinstance(eth_price, dict) else 0

    def gwei_to_usd(gwei, gas_units):
        try:
            return round(float(gwei) * gas_units * 1e-9 * eth_usd, 4)
        except:
            return None

    safe   = g.get("SafeGasPrice", "0")
    prop   = g.get("ProposeGasPrice", "0")
    fast   = g.get("FastGasPrice", "0")
    base   = g.get("suggestBaseFee", "0")

    return {
        "timestamp": ts(),
        "eth_price_usd": eth_usd,
        "gas_prices_gwei": {
            "base_fee": base,
            "safe": safe,
            "standard": prop,
            "fast": fast
        },
        "estimated_cost_usd": {
            "simple_transfer_21k_gas": {
                "safe": gwei_to_usd(safe, 21000),
                "standard": gwei_to_usd(prop, 21000),
                "fast": gwei_to_usd(fast, 21000)
            },
            "erc20_transfer_65k_gas": {
                "safe": gwei_to_usd(safe, 65000),
                "standard": gwei_to_usd(prop, 65000),
                "fast": gwei_to_usd(fast, 65000)
            },
            "uniswap_swap_150k_gas": {
                "safe": gwei_to_usd(safe, 150000),
                "standard": gwei_to_usd(prop, 150000),
                "fast": gwei_to_usd(fast, 150000)
            }
        },
        "source": "Etherscan Gas Oracle + CoinGecko"
    }

async def handle_protocol_tvl(args):
    """Ethereum DeFi protocol TVL intelligence from DefiLlama"""
    protocol = args.get("protocol", "").strip().lower()
    if not protocol:
        # Return top Ethereum protocols
        all_p = await get(f"{LLAMA}/protocols")
        eth_p = []
        if isinstance(all_p, list):
            for p in all_p:
                if "Ethereum" in p.get("chains", []):
                    tvl_raw_p = p.get("tvl")
                    tvl_p = tvl_raw_p[-1].get("totalLiquidityUSD") if isinstance(tvl_raw_p, list) and tvl_raw_p else tvl_raw_p
                    eth_p.append({
                        "name": p.get("name"),
                        "slug": p.get("slug"),
                        "tvl_usd": tvl_p,
                        "category": p.get("category"),
                        "change_7d": p.get("change_7d")
                    })
            eth_p.sort(key=lambda x: x.get("tvl_usd") or 0, reverse=True)
        return {"top_ethereum_protocols": eth_p[:20], "count": len(eth_p), "timestamp": ts(), "source": "DefiLlama"}

    data = await get(f"{LLAMA}/protocol/{protocol}")
    if isinstance(data, dict) and "error" not in data:
        chains = data.get("chainTvls", {})
        eth_tvl = chains.get("Ethereum", {}).get("tvl", [{}])
        latest_tvl = eth_tvl[-1].get("totalLiquidityUSD", 0) if eth_tvl else 0
        tvl_raw = data.get("tvl")
        tvl_current = tvl_raw[-1].get("totalLiquidityUSD") if isinstance(tvl_raw, list) and tvl_raw else tvl_raw
        return {
            "protocol": data.get("name"),
            "category": data.get("category"),
            "tvl_total_usd": tvl_current,
            "tvl_ethereum_usd": latest_tvl,
            "chains": list(chains.keys()),
            "change_1d": data.get("change_1d"),
            "change_7d": data.get("change_7d"),
            "audits": data.get("audits"),
            "timestamp": ts(),
            "source": "DefiLlama"
        }
    return {"error": f"Protocol '{protocol}' not found", "timestamp": ts()}

async def handle_erc4626_vault(args):
    """ERC-4626 tokenized vault analysis: yield, TVL, risk assessment"""
    vaults = await get(f"{LLAMA_Y}/pools")
    if isinstance(vaults, dict):
        data = vaults.get("data", [])
    else:
        return {"error": "Could not fetch vault data"}

    chain_filter = args.get("chain", "Ethereum").lower()
    min_tvl = args.get("min_tvl_usd", 1000000)
    max_results = min(args.get("limit", 20), 50)

    eth_vaults = []
    for v in data:
        if v.get("chain", "").lower() == chain_filter and v.get("tvlUsd", 0) >= min_tvl:
            apy = v.get("apy") or 0
            tvl = v.get("tvlUsd") or 0
            score = 50
            if tvl > 100_000_000: score += 20
            elif tvl > 10_000_000: score += 10
            if 0 < apy < 30: score += 10
            elif apy > 50: score -= 20
            if v.get("ilRisk") == "yes": score -= 15
            eth_vaults.append({
                "pool": v.get("pool"),
                "project": v.get("project"),
                "symbol": v.get("symbol"),
                "apy_pct": round(apy, 2),
                "tvl_usd": round(tvl, 0),
                "il_risk": v.get("ilRisk"),
                "risk_score": score,
                "risk_grade": risk_grade(score),
            })

    eth_vaults.sort(key=lambda x: x.get("tvl_usd", 0), reverse=True)
    return {
        "chain": chain_filter,
        "min_tvl_usd": min_tvl,
        "vaults": eth_vaults[:max_results],
        "total_found": len(eth_vaults),
        "timestamp": ts(),
        "source": "DefiLlama Yields"
    }

async def handle_rwa_tokenization(args):
    """Real-world asset tokenization intelligence on Ethereum"""
    RWA_PROTOCOLS = [
        "ondo-finance", "maple-finance", "centrifuge", "goldfinch",
        "backed-finance", "securitize", "superstate", "openeden",
        "mountain-protocol", "matrixdock"
    ]
    slug = args.get("protocol", "").strip().lower()
    if slug:
        data = await get(f"{LLAMA}/protocol/{slug}")
        if isinstance(data, dict) and "error" not in data:
            return {
                "protocol": data.get("name"),
                "category": data.get("category"),
                "description": data.get("description", "")[:300],
                "tvl_usd": data.get("tvl"),
                "chains": data.get("chains", []),
                "audits": data.get("audits"),
                "change_7d": data.get("change_7d"),
                "timestamp": ts(),
                "source": "DefiLlama"
            }
        return {"error": f"Protocol '{slug}' not found"}

    # Overview of known RWA protocols
    results = []
    for slug in RWA_PROTOCOLS:
        d = await get(f"{LLAMA}/protocol/{slug}")
        if isinstance(d, dict) and "error" not in d and d.get("tvl"):
            tvl_r = d.get("tvl")
            tvl_curr = tvl_r[-1].get("totalLiquidityUSD") if isinstance(tvl_r, list) and tvl_r else tvl_r
            results.append({
                "protocol": d.get("name"),
                "category": d.get("category"),
                "tvl_usd": tvl_curr,
                "chains": d.get("chains", [])[:3],
                "change_7d": d.get("change_7d")
            })
    results.sort(key=lambda x: x.get("tvl_usd") or 0, reverse=True)
    return {
        "rwa_protocols_on_ethereum": results,
        "total_rwa_tvl_usd": sum(r.get("tvl_usd") or 0 for r in results),
        "timestamp": ts(),
        "note": "Covers tokenized treasuries, bonds, credit, commodities on Ethereum",
        "source": "DefiLlama"
    }

async def handle_stablecoin_check(args):
    """Ethereum stablecoin peg health and risk check"""
    symbol = args.get("symbol", "USDC").upper()
    STABLECOINS = {
        "USDC": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "USDT": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "DAI":  "0x6b175474e89094c44da98b954eedeac495271d0f",
        "FRAX": "0x853d955acef822db058eb8505911ed77f175b99e",
        "LUSD": "0x5f98805a4e8be255a32880fdec7f6728c6568ba0",
        "PYUSD":"0x6c3ea9036406852006290770bedfcaba0e23a0e8",
        "RLUSD":"0x8292bb45bf1ee4d140127f69a6d9f3f9b0a5c86d",
    }
    contract = STABLECOINS.get(symbol) or args.get("contract_address", "")
    if not contract:
        return {"known_stablecoins": list(STABLECOINS.keys()),
                "message": "Provide symbol or contract_address"}

    price_data = await get(f"{CG}/simple/token_price/ethereum",
                           {"contract_addresses": contract, "vs_currencies": "usd",
                            "include_24hr_change": "true"})
    price = None
    change = None
    if isinstance(price_data, dict):
        token_data = price_data.get(contract.lower(), {})
        price = token_data.get("usd")
        change = token_data.get("usd_24h_change")

    peg_dev = abs(price - 1.0) if price else None
    peg_status = "STABLE" if peg_dev is not None and peg_dev < 0.005 else \
                 "MINOR_DEVIATION" if peg_dev is not None and peg_dev < 0.02 else "DEPEGGED"

    score = 90 if peg_status == "STABLE" else 50 if peg_status == "MINOR_DEVIATION" else 10

    return {
        "symbol": symbol,
        "contract": contract,
        "price_usd": price,
        "peg_deviation": round(peg_dev, 6) if peg_dev is not None else None,
        "peg_deviation_pct": round(peg_dev * 100, 4) if peg_dev is not None else None,
        "peg_status": peg_status,
        "change_24h_pct": round(change, 4) if change else None,
        "risk_score": score,
        "risk_grade": risk_grade(score),
        "timestamp": ts(),
        "source": "CoinGecko on-chain price"
    }

async def handle_wallet_intel(args):
    """Ethereum wallet intelligence: balance, token holdings, recent activity"""
    address = args.get("address", "").strip()
    if not address:
        return {"error": "address required"}

    bal_hex, tokens, txs = await asyncio.gather(
        eth_rpc("eth_getBalance", [address, "latest"]),
        etherscan({"module": "account", "action": "tokentx",
                   "address": address, "page": "1", "offset": "20", "sort": "desc"}),
        etherscan({"module": "account", "action": "txlist",
                   "address": address, "page": "1", "offset": "10",
                   "sort": "desc", "startblock": "0", "endblock": "99999999"}),
    )
    eth_bal = wei_to_eth(bal_hex) if bal_hex else 0
    eth_price = await get(f"{CG}/simple/price", {"ids": "ethereum", "vs_currencies": "usd"})
    eth_usd = eth_price.get("ethereum", {}).get("usd", 0) if isinstance(eth_price, dict) else 0

    token_set = {}
    if isinstance(tokens, dict) and tokens.get("status") == "1":
        for tx in (tokens.get("result") or []):
            sym = tx.get("tokenSymbol", "?")
            if sym not in token_set:
                token_set[sym] = {"symbol": sym, "name": tx.get("tokenName"),
                                  "contract": tx.get("contractAddress"),
                                  "decimals": tx.get("tokenDecimal")}

    recent_txs = []
    if isinstance(txs, dict) and txs.get("status") == "1":
        for tx in (txs.get("result") or [])[:5]:
            recent_txs.append({
                "hash": tx.get("hash"),
                "from": tx.get("from"),
                "to": tx.get("to"),
                "value_eth": round(int(tx.get("value", "0")) / 1e18, 6),
                "timestamp": datetime.fromtimestamp(
                    int(tx.get("timeStamp", 0)), tz=timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ")
            })

    return {
        "address": address,
        "eth_balance": round(eth_bal, 6),
        "eth_balance_usd": round(eth_bal * eth_usd, 2),
        "token_types": len(token_set),
        "known_tokens": list(token_set.values())[:15],
        "recent_transactions": recent_txs,
        "timestamp": ts(),
        "source": "Etherscan + CoinGecko"
    }

async def handle_defi_yields(args):
    """Top DeFi yield opportunities on Ethereum"""
    chain = args.get("chain", "Ethereum")
    min_tvl = args.get("min_tvl_usd", 5_000_000)
    min_apy = args.get("min_apy_pct", 0)
    max_apy = args.get("max_apy_pct", 100)
    limit = min(args.get("limit", 20), 50)

    pools = await get(f"{LLAMA_Y}/pools")
    data = pools.get("data", []) if isinstance(pools, dict) else []

    results = []
    for p in data:
        if (p.get("chain", "").lower() == chain.lower() and
            p.get("tvlUsd", 0) >= min_tvl and
            min_apy <= (p.get("apy") or 0) <= max_apy):
            results.append({
                "pool": p.get("pool"),
                "project": p.get("project"),
                "symbol": p.get("symbol"),
                "apy_pct": round(p.get("apy") or 0, 2),
                "apy_base": round(p.get("apyBase") or 0, 2),
                "apy_reward": round(p.get("apyReward") or 0, 2),
                "tvl_usd": round(p.get("tvlUsd") or 0, 0),
                "il_risk": p.get("ilRisk"),
                "exposure": p.get("exposure"),
            })

    results.sort(key=lambda x: x.get("tvl_usd", 0), reverse=True)
    return {
        "chain": chain,
        "filters": {"min_tvl_usd": min_tvl, "min_apy": min_apy, "max_apy": max_apy},
        "yields": results[:limit],
        "total_found": len(results),
        "timestamp": ts(),
        "source": "DefiLlama Yields"
    }

# ── Server Setup ────────────────────────────────────────



def build_server():
    server = WhitelabelMCPServer(
        product_name=PRODUCT_NAME,
        product_slug="ethoracle",
        version=VERSION,
        port_mcp=PORT_MCP,
        port_health=PORT_HEALTH,
    )
    server.register_tool("eth_overview", "Ethereum ecosystem overview: ETH price, gas fees, TVL, block stats",
        {"type": "object", "properties": {}, "required": []}, handle_overview)
    server.register_tool("eth_token_risk",
        "ERC-20 token risk assessment: holder concentration, contract age, liquidity signals",
        {"type": "object", "properties": {"contract_address": {"type": "string", "description": "ERC-20 token contract address (0x...)"}}, "required": ["contract_address"]}, handle_token_risk)
    server.register_tool("eth_contract_verify",
        "Verify Ethereum smart contract: source code, ABI, compiler, proxy detection",
        {"type": "object", "properties": {"contract_address": {"type": "string", "description": "Smart contract address (0x...)"}}, "required": ["contract_address"]}, handle_contract_verify)
    server.register_tool("eth_gas",
        "Real-time Ethereum gas oracle with USD cost estimates for common operations",
        {"type": "object", "properties": {}, "required": []}, handle_gas)
    server.register_tool("eth_protocol_tvl",
        "Ethereum DeFi protocol TVL intelligence. Leave protocol empty for top-20 list.",
        {"type": "object", "properties": {"protocol": {"type": "string", "description": "Protocol slug (e.g. uniswap, aave, lido) or empty for top-20"}}, "required": []}, handle_protocol_tvl)
    server.register_tool("eth_erc4626_vaults",
        "ERC-4626 tokenized vault analysis: yield, TVL, risk scoring",
        {"type": "object", "properties": {"chain": {"type": "string", "default": "Ethereum"}, "min_tvl_usd": {"type": "number", "default": 1000000}, "limit": {"type": "integer", "default": 20}}, "required": []}, handle_erc4626_vault)
    server.register_tool("eth_rwa_tokenization",
        "Real-world asset tokenization intelligence: tokenized bonds, treasuries, credit on Ethereum",
        {"type": "object", "properties": {"protocol": {"type": "string", "description": "RWA protocol slug or empty for full overview"}}, "required": []}, handle_rwa_tokenization)
    server.register_tool("eth_stablecoin_check",
        "Ethereum stablecoin peg health and risk check (USDC, USDT, DAI, FRAX, PYUSD, RLUSD...)",
        {"type": "object", "properties": {"symbol": {"type": "string"}, "contract_address": {"type": "string"}}, "required": []}, handle_stablecoin_check)
    server.register_tool("eth_wallet_intel",
        "Ethereum wallet intelligence: ETH balance, token holdings, recent transactions",
        {"type": "object", "properties": {"address": {"type": "string", "description": "Ethereum wallet address (0x...)"}}, "required": ["address"]}, handle_wallet_intel)
    server.register_tool("eth_defi_yields",
        "Top DeFi yield opportunities on Ethereum filtered by TVL, APY range",
        {"type": "object", "properties": {"chain": {"type": "string", "default": "Ethereum"}, "min_tvl_usd": {"type": "number", "default": 5000000}, "min_apy_pct": {"type": "number", "default": 0}, "max_apy_pct": {"type": "number", "default": 100}, "limit": {"type": "integer", "default": 20}}, "required": []}, handle_defi_yields)
    return server

if __name__ == "__main__":
    srv = build_server()
    srv.run()
