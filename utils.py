import base64

# --- Simple Encryption Helper ---
# Not military grade, but prevents plain text reading
ENC_KEY = "PlaylisterAppSecretKey"

def parse_views(view_text):
    """
    '1.5M views', '300K plays' gibi metinleri sayıya çevirir.
    """
    if not view_text:
        return 0
    
    text = str(view_text).lower()
    for suffix in [" views", " plays", " hits", " subscribers", " abone"]:
        text = text.replace(suffix, "")
    text = text.strip()
    
    multiplier = 1
    if text.endswith("b"):
        multiplier = 1_000_000_000
        text = text[:-1]
    elif text.endswith("m"):
        multiplier = 1_000_000
        text = text[:-1]
    elif text.endswith("k"):
        multiplier = 1_000
        text = text[:-1]
        
    try:
        text = text.replace(",", ".")
        return int(float(text) * multiplier)
    except ValueError:
        return 0

def encrypt_text(text):
    if not text: return ""
    try:
        # Simple XOR
        chars = []
        key_len = len(ENC_KEY)
        for i, char in enumerate(text):
            x = ord(char) ^ ord(ENC_KEY[i % key_len])
            chars.append(chr(x))
        return base64.b64encode("".join(chars).encode('utf-8')).decode('utf-8')
    except:
        return text

def decrypt_text(text):
    if not text: return ""
    try:
        # Decode Base64
        decoded = base64.b64decode(text.encode('utf-8')).decode('utf-8')
        chars = []
        key_len = len(ENC_KEY)
        for i, char in enumerate(decoded):
            x = ord(char) ^ ord(ENC_KEY[i % key_len])
            chars.append(chr(x))
        return "".join(chars)
    except:
        return ""
