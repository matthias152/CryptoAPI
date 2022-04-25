from django.shortcuts import render
from pycoingecko import CoinGeckoAPI
from .models import CryptoWallet, Balance, Transaction, BuyPrice
from .forms import NewUserForm
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from datetime import date, time, datetime


coingecko = CoinGeckoAPI()

today = date.today()
cryptos = CryptoWallet.objects.all()
balances = Balance.objects.all()
transcactions = Transaction.objects.all()
buy_prices = BuyPrice.objects.all()
user_cryptos_list = []
user_profitloss_dict = {}
profit_loss_final = []


def get_coin_price(coin):
    c = coingecko.get_price(ids=str(coin).lower(), vs_currencies='usd')[str(coin).lower()]['usd']
    return float(c)


def CreateBuyTransaction(user, day, time, bcoin, type, qb, bce, ufb):
    new_transaction = Transaction()
    new_transaction.user = user
    new_transaction.day_created = day
    new_transaction.time_created = time
    new_transaction.coin = bcoin
    new_transaction.type = type
    new_transaction.quantityCrypto = float(qb) / float(bce)
    new_transaction.price = bce
    new_transaction.balance_after = ufb - float(qb)
    new_transaction.save()


def CreateSellTransaction(user, day, time, scoin, type, sq, sce, ufb):
    new_transaction = Transaction()
    new_transaction.user = user
    new_transaction.day_created = day
    new_transaction.time_created = time
    new_transaction.coin = scoin
    new_transaction.type = type
    new_transaction.quantityCrypto = sq
    new_transaction.price = sce
    new_transaction.balance_after = ufb + float(sq) * float(sce)
    new_transaction.save()


def CollectBuyPrices(user, day, time, crypto, cq, price):
    bPrice = BuyPrice()
    bPrice.user = user
    bPrice.day_created = day
    bPrice.time_created = time
    bPrice.cryptoName = crypto
    bPrice.cryptoQuantity = cq
    bPrice.price = price
    bPrice.save()


def register_request(request):
    if request.method == 'POST':
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return render(request, 'index.html')
        messages.error(request, "Unsuccessful registration. Invalid information.")
    form = NewUserForm()
    return render(
        request=request, template_name="register.html", context={"register_form": form})


class CustomLoginView(LoginView):
    template_name = 'login.html'
    fields = '__all__'
    redirect_authenticated_user = True

    def get_success_url(self):
        return ('http://127.0.0.1:8000/')

@login_required(login_url='http://127.0.0.1:8000/login')
def wallet_test(request):
    profit_loss_all = {}
    user_cryptos = buy_prices.filter(user=request.user)
    
    for i in user_cryptos:
        profit_loss = (i.cryptoQuantity * get_coin_price(i.cryptoName)) - (i.cryptoQuantity * i.price)
        profit_loss_all[str(i.cryptoName)] = profit_loss
    
    print(profit_loss_all)

    return render(request, "wallet_test.html", {
        'profit_loss_all': profit_loss_all.items(),
    }) 
 
@login_required(login_url='http://127.0.0.1:8000/login')
def wallet(request):
    TRENDING_COINS = []
    current_crypto_values = []
    profit_loss = []
    trends = coingecko.get_search_trending()['coins']
    user_final_balance = float(balances.get(user=request.user).balance)
    user_cryptos = cryptos.filter(user=request.user)
    user_prices = buy_prices.filter(user=request.user)

    for i in user_prices:
        if str(i.cryptoName) not in user_profitloss_dict:
            user_profitloss_dict[str(i.cryptoName)] = []

    for j in user_prices:
        profit_losss = j.cryptoQuantity * get_coin_price(j.cryptoName) - j.cryptoQuantity * j.price
        user_profitloss_dict[str(j.cryptoName)].append(float(profit_losss))

    for i in user_profitloss_dict:
        z = user_profitloss_dict[i]
        y = sum(z)
        profit_loss_final.append(y)

    for i in user_cryptos:
        z = round(get_coin_price(i.cryptoName) * i.cryptoQuantity - i.quantityDollars, 3)
        profit_loss.append(z)

    for i in user_cryptos:
        z = round(get_coin_price(i.cryptoName) * i.cryptoQuantity, 5)
        current_crypto_values.append(z)

    for i in range(7):
        coin = trends[i]['item']['name']
        TRENDING_COINS.append(coin)

    return render(request, "index.html", {
        'trending': TRENDING_COINS,
        'ALL_CRYPTOS': cryptos,
        'current_crypto_values': current_crypto_values,
        'user_cryptos': user_cryptos,
        'user_final_balance': user_final_balance,
        'user': request.user,
        'test': user_profitloss_dict,
        'profit_loss': profit_loss_final,
    })


@login_required(login_url='http://127.0.0.1:8000/login')
def buy_cryptos(request):
    if request.method == 'POST':
        if request.POST.get('cryptoNameBuy') and request.POST.get('quantityDollarsBuy'):
            user_balance = balances.get(user=request.user)
            user_final_balance = float(user_balance.balance)
            user_cryptos = cryptos.filter(user=request.user)
            buying_coin = request.POST.get('cryptoNameBuy', None)
            buying_coin_exchange = get_coin_price(buying_coin)
            quantity_bought = request.POST.get('quantityDollarsBuy')
            cryptoQuantityBought = float(quantity_bought) / float(buying_coin_exchange)

        for i in user_cryptos:
            z = str(i.cryptoName)
            user_cryptos_list.append(z)
        if float(quantity_bought) <= user_final_balance:
            if str(buying_coin) in user_cryptos_list:
                y = user_cryptos.get(cryptoName=buying_coin)
                y.cryptoQuantity += float(quantity_bought) / float(buying_coin_exchange)
                y.quantityDollars += float(quantity_bought)
                y.save()
                user_balance.balance -= float(quantity_bought)
                user_balance.save()
                curr_time = datetime.now().time()
                CreateBuyTransaction(request.user, today, curr_time,
                    buying_coin, "buy", quantity_bought, buying_coin_exchange, user_final_balance)
                CollectBuyPrices(request.user, today, curr_time, buying_coin, cryptoQuantityBought, buying_coin_exchange)
                return render(request, 'buy-crypto.html')
            else:
                new_cryp = CryptoWallet()
                new_cryp.user = request.user
                new_cryp.cryptoName = buying_coin
                new_cryp.quantityDollars = quantity_bought
                new_cryp.cryptoQuantity = float(quantity_bought) / float(buying_coin_exchange)
                new_cryp.save()
                user_balance.balance -= float(quantity_bought)
                user_balance.save()
                curr_time = datetime.now().time()
                CreateBuyTransaction(request.user, today, curr_time,
                    buying_coin, "buy", quantity_bought, buying_coin_exchange, user_final_balance)
                CollectBuyPrices(request.user, today, curr_time, buying_coin, cryptoQuantityBought, buying_coin_exchange)
                return render(request, 'buy-crypto.html')
        return render(request, 'buy-crypto.html')
    return render(request, 'buy-crypto.html')


@login_required(login_url='http://127.0.0.1:8000/login')
def sell_cryptos(request):
    if request.method == 'POST':
        if request.POST.get('cryptoNameSell') and request.POST.get('cryptoQuantitySell'):
            user_balance = balances.get(user=request.user)
            user_final_balance = float(user_balance.balance)
            user_cryptos = cryptos.filter(user=request.user)
            selling_coin = request.POST.get('cryptoNameSell')
            selling_quantity = request.POST.get('cryptoQuantitySell')
            selling_coin_exchange = get_coin_price(selling_coin)
            y = user_cryptos.get(cryptoName=selling_coin)
            user_prices = buy_prices.filter(user=request.user, cryptoName=selling_coin)
            testing = float(selling_quantity)

            for i in user_cryptos:
                z = str(i.cryptoName)
                user_cryptos_list.append(z)
            if str(selling_coin) in user_cryptos_list:
                if float(y.cryptoQuantity) >= float(selling_quantity):
                    y.cryptoQuantity -= float(selling_quantity)
                    y.save()
                    if y.cryptoQuantity == 0:
                        y.delete()
                    user_balance.balance += float(selling_quantity) * float(selling_coin_exchange)
                    user_balance.save()
                    curr_time = datetime.now().time()
                    CreateSellTransaction(request.user, today, curr_time, selling_coin, "sell",
                        selling_quantity, selling_coin_exchange, user_final_balance)
                        # something is not yes in this algorithm
                    for i in user_prices:
                        for j in user_prices[1:]:
                            if testing > i.cryptoQuantity:
                                testing = testing - i.cryptoQuantity
                                i.delete()
                                j.cryptoQuantity -= testing
                                j.save()
                                if testing < 0:
                                    break
                                else:
                                    continue
                            else:
                                i.cryptoQuantity -= testing
                                i.save()

                    return render(request, 'sell-crypto.html')
                else:
                    return render(request, 'sell-crypto.html')
            else:
                return render(request, 'sell-crypto.html')
        return render(request, 'sell-crypto.html')
    return render(request, 'sell-crypto.html')


@login_required(login_url='http://127.0.0.1:8000/login')
def transactions(request):
    user_transactions = transcactions.filter(user=request.user)
    return render(request, 'transactions.html', {
        'transactions': user_transactions,
    })
