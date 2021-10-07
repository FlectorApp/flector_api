from web3 import Web3
import os
import json
import re
import requests
import datetime
from pycoingecko import CoinGeckoAPI
from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


cg = CoinGeckoAPI()
bep20_dev_wallet = '0xFc670D1D34c83Cf59A678a513c50F41360cFE6Ae'
Contract = '0xD6ca9451bba47e26706A701aE05bE45A712D4B1B' # ADAFlect Contract
BSC_API = os.environ['BSC_API_KEY']
bsc = 'https://bsc-dataseed.binance.org/'

@app.get("/rewards/{wallet}")
def read_(wallet: str, currency: str = 'usd'):
    return ada(wallet, currency)


def ada(wallet, currency):
    ada = cg.get_price(ids='cardano', vs_currencies=currency,include_24hr_change='true')
    price_usd = ada['cardano'][currency]
    change_24h = round(ada['cardano'][currency+'_24h_change'],2)
    web3 = Web3(Web3.HTTPProvider(bsc))
    contract_address = web3.toChecksumAddress(Contract)
    r = requests.get(url = 'https://api.bscscan.com/api?module=contract&action=getabi&address='+Contract+'&apikey='+BSC_API)
    response = r.json()
    abi=json.loads(response['result'])
    contract = web3.eth.contract(address=contract_address, abi=abi)
    dividendsInfo = contract.functions.getAccountDividendsInfo(wallet).call()
    pending_ada = int(dividendsInfo[3])/1000000000000000000
    pending_usd = pending_ada * price_usd
    total_ada = int(dividendsInfo[4])/1000000000000000000
    total_usd = total_ada * price_usd
    last_reward_date = datetime.datetime.utcfromtimestamp(dividendsInfo[5])
    last_reward_hours = int(divmod((datetime.datetime.now() - last_reward_date).total_seconds(), 3600)[0])
    return {"ada_price_usd": price_usd, "ada_change_24h": change_24h, "pending_ada": pending_ada, "pending_usd":pending_usd,"total_ada":total_ada,"total_usd":total_usd,"last_reward_date":last_reward_date,"last_reward_hours":last_reward_hours, "currency":currency, "bep20_dev_wallet": bep20_dev_wallet}

@app.get("/cg/price")
def read_(ids: str, currency: str = 'usd'):
    return cg.get_price(ids=ids, vs_currencies=currency,include_24hr_change='true', include_24hr_vol='true', include_last_updated_at='true', include_market_cap='true')