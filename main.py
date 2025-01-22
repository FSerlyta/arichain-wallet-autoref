import requests
import random
import time
import string
from colorama import Fore, Style, init
from datetime import datetime
from bs4 import BeautifulSoup

init()

ANDROID_USER_AGENTS = [
    'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
    # Add more user agents as needed
]

class TempMailClient:
    def __init__(self, proxy_dict=None):
        self.base_url = "https://smailpro.com/app"
        self.inbox_url = "https://app.sonjj.com/v1/temp_gmail"
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': random.choice(ANDROID_USER_AGENTS),
            'origin': 'https://smailpro.com',
            'referer': 'https://smailpro.com/'
        }
        self.proxy_dict = proxy_dict
        self.email_address = None
        self.key = None
        self.payload = None

    def create_email(self) -> dict:
        url = f"{self.base_url}/create"
        params = {
            'username': 'random',
            'type': 'alias',
            'domain': 'gmail.com',
            'server': '1'
        }
        
        response = requests.get(url, params=params, headers=self.headers, proxies=self.proxy_dict)
        data = response.json()
        
        self.email_address = data['address']
        self.key = data['key']
        
        return data

    def create_inbox(self) -> dict:
        url = f"{self.base_url}/inbox"
        payload = [{
            "address": self.email_address,
            "timestamp": int(time.time()),
            "key": self.key
        }]
        
        response = requests.post(url, json=payload, headers=self.headers, proxies=self.proxy_dict)
        data = response.json()
        
        if data:
            self.payload = data[0]['payload']
        
        return data[0]

    def get_inbox(self) -> dict:
        url = f"{self.inbox_url}/inbox"
        params = {'payload': self.payload}
        
        response = requests.get(url, params=params, headers=self.headers, proxies=self.proxy_dict)
        return response.json()

    def get_message_token(self, mid: str) -> str:
        url = f"{self.base_url}/message"
        params = {
            'email': self.email_address,
            'mid': mid
        }
        
        response = requests.get(url, params=params, headers=self.headers, proxies=self.proxy_dict)
        return response.text

    def get_message_content(self, token: str) -> dict:
        url = f"{self.inbox_url}/message"
        params = {'payload': token}
        
        response = requests.get(url, params=params, headers=self.headers, proxies=self.proxy_dict)
        return response.json()

    def extract_otp(self, html_content: str) -> str:
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            otp_element = soup.find('b', style=lambda value: value and 'letter-spacing:16px' in value)
            if otp_element:
                return otp_element.text.strip()
            return None
        except Exception as e:
            log(f"Error extracting OTP: {e}", Fore.RED)
            return None

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(message, color=Fore.WHITE, current=None, total=None):
    timestamp = f"[{Fore.LIGHTBLACK_EX}{get_timestamp()}{Style.RESET_ALL}]"
    progress = f"[{Fore.LIGHTBLACK_EX}{current}/{total}{Style.RESET_ALL}]" if current is not None and total is not None else ""
    print(f"{timestamp} {progress} {color}{message}{Style.RESET_ALL}")

def ask(message):
    return input(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")

def load_proxies():
    try:
        with open("proxies.txt", "r") as file:
            proxies = [line.strip() for line in file if line.strip()]
        print(f"{Fore.GREEN}\nLoaded {len(proxies)} proxies{Style.RESET_ALL}")
        return proxies
    except FileNotFoundError:
        print(f"{Fore.RED}\nFile proxies.txt not found{Style.RESET_ALL}")
        return []

def get_random_proxy(proxies):
    return random.choice(proxies) if proxies else None

def generate_password():
    word = ''.join(random.choices(string.ascii_letters, k=5))
    numbers = ''.join(random.choices(string.digits, k=3))
    return f"{word.capitalize()}@{numbers}#"

def send_otp(email, proxy_dict, headers, current=None, total=None):
    url = "https://arichain.io/api/email/send_valid_email"
    payload = {
        'blockchain': "testnet",
        'email': email,
        'lang': "en",
        'device': "app",
        'is_mobile': "Y"
    }
    try:
        response = requests.post(url, data=payload, headers=headers, proxies=proxy_dict, timeout=120)
        response.raise_for_status()
        log(f"OTP code sent to {email}", Fore.YELLOW, current, total)
        return True
    except requests.RequestException as e:
        log(f"Failed to send OTP: {e}", Fore.RED, current, total)
        return False

def verify_otp(email, valid_code, password, proxy_dict, invite_code, headers, current=None, total=None):
    url = "https://arichain.io/api/account/signup_mobile"
    payload = {
        'blockchain': "testnet",
        'email': email,
        'valid_code': valid_code,
        'pw': password,
        'pw_re': password,
        'invite_code': invite_code,
        'lang': "en",
        'device': "app",
        'is_mobile': "Y"
    }

    try:
        response = requests.post(url, data=payload, headers=headers, proxies=proxy_dict, timeout=120)
        response.raise_for_status()
        result = response.json()
        log(f"Success Register with referral code {invite_code}", Fore.GREEN, current, total)

        with open("accounts.txt", "a") as file:
            file.write(f"ID: {result['result']['session_code']}\nEmail: {email}\nPassword: {password}\nAddress: {result['result']['address']}\nPrivate Key: {result['result']['master_key']}\n\n")

        return result['result']['address']

    except requests.RequestException as e:
        log(f"Failed to verify OTP: {e}", Fore.RED, current, total)
        return None

def daily_claim(address, proxy_dict, headers, current=None, total=None):
    url = "https://arichain.io/api/event/checkin"
    payload = {
        'blockchain': "testnet",
        'address': address,
        'lang': "en",
        'device': "app",
        'is_mobile': "Y"
    }

    try:
        response = requests.post(url, data=payload, headers=headers, proxies=proxy_dict, timeout=120)
        response.raise_for_status()
        data = response.json()

        if data.get('status') == 'success':
            log("Success claim Daily", Fore.GREEN, current, total)
            return True
        log("Daily claim failed", Fore.RED, current, total)
        return False
    except requests.exceptions.RequestException as e:
        log(f"Daily claim error: {str(e)}", Fore.RED, current, total)
        return False

def auto_send(email, to_address, password, proxy_dict, headers, current=None, total=None):
    url = "https://arichain.io/api/wallet/transfer_mobile"
    
    payload = {
        'blockchain': "testnet",
        'symbol': "ARI",
        'email': email,
        'to_address': to_address,
        'pw': password,
        'amount': "60",
        'memo': "",
        'valid_code': "",
        'lang': "en",
        'device': "app",
        'is_mobile': "Y"
    }

    try:
        response = requests.post(url, data=payload, headers=headers, proxies=proxy_dict, timeout=120)
        response.raise_for_status()
        result = response.json()
        
        if result.get("status") == "success" and result.get("result") == "success":
            log(f"Success sent 60 ARI to {to_address}", Fore.GREEN, current, total)
            return True
        else:
            log(f"Failed to send: {result}", Fore.RED, current, total)
            return False
            
    except requests.RequestException as e:
        log(f"Auto-send failed: {e}", Fore.RED, current, total)
        return False

def print_banner():
    print(Fore.CYAN + """
╔═══════════════════════════════════════════╗
║         Defas Wallet Autoreferral           ║
║       https://github.com/FSerlyta        ║
╚═══════════════════════════════════════════╝
    """ + Style.RESET_ALL)

def main():
    proxies = load_proxies()

    if not proxies:
        return

    # Ask for input parameters
    amount = ask("How many referrals would you like to process? ")
    invite_code = ask("Enter referral invite code: ")

    for idx in range(int(amount)):
        proxy = get_random_proxy(proxies)
        log(f"Processing referral {idx + 1}/{amount}", Fore.GREEN)

        if not proxy:
            log("No proxies available, skipping...", Fore.RED)
            continue

        # Create email, send OTP, verify and register
        client = TempMailClient(proxy_dict={"http": proxy, "https": proxy})
        data = client.create_email()
        email = data.get("address")

        if send_otp(email, proxy_dict={"http": proxy, "https": proxy}, headers=client.headers, current=idx + 1, total=int(amount)):
            mid = client.create_inbox().get('mid')
            token = client.get_message_token(mid)
            message = client.get_message_content(token)
            otp_code = client.extract_otp(message.get("html_content"))

            if otp_code:
                address = verify_otp(email, otp_code, generate_password(), proxy_dict={"http": proxy, "https": proxy},
                                     invite_code=invite_code, headers=client.headers, current=idx + 1, total=int(amount))
                if address:
                    daily_claim(address, proxy_dict={"http": proxy, "https": proxy}, headers=client.headers, current=idx + 1, total=int(amount))
                    auto_send(email, to_address="address_to_send_ari", password="password", proxy_dict={"http": proxy, "https": proxy},
                              headers=client.headers, current=idx + 1, total=int(amount))

if __name__ == '__main__':
    print_banner()
    main()
