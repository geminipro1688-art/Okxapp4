import streamlit as st
import requests
import numpy as np
from PIL import Image
import io
import base64
import datetime

# === 設定頁面 ===
st.set_page_config(
    page_title="霓虹新聞速報產生器",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === 常數與預設資料 ===
FOOTER_PRESETS = [
    "週末交易怕滑點？快用 OKX Wallet DEX 聚合，最優匯率一鍵換！",
    "OKX Wallet 支援百條公鏈，跨鏈交易一鍵搞定，省時又省力。",
    "Web3 入口首選 OKX Wallet，安全探索 DeFi 與 NFT 世界。",
    "擔心私鑰遺失？OKX MPC 錢包助你輕鬆管理，資產安全更升級。",
    "OKX Earn 提供多元理財方案，讓閒置資產也能穩健增值。",
    "隨時隨地，OKX App 讓你輕鬆掌握市場脈動，交易快人一步。",
    "OKX Web3 錢包，聚合全網流動性，是你衝土狗的最佳利器。",
    "鏈上交互多留心，不明連結千萬別點擊！",
    "行情波動劇烈，合約開單請務必設置止損。",
    "私鑰助記詞不離身，資產安全自己掌握。",
    "Gas Fee 波動大，建議避開壅塞時段操作。",
    "DEX 交易雖然自由，但也別忘了預留 Gas 費。",
    "DeFi 挖礦高收益伴隨高風險，無常損失要精算。",
    "跨鏈橋選擇多，盡量選擇官方橋樑最穩妥。",
    "迷因幣波動劇烈，投資前請做好功課 (DYOR)。",
    "牛市不言頂，熊市不言底，定期定額最安心。",
    "週末流動性較差，大額交易請注意滑點衝擊。"
]

TOKEN_MAPPING = {
    'btc': 'btc', 'bitcoin': 'btc', '比特幣': 'btc',
    'eth': 'eth', 'ethereum': 'eth', '以太坊': 'eth',
    'sol': 'sol', 'solana': 'sol',
    'doge': 'doge', 'dogecoin': 'doge',
    'usdt': 'usdt', 'usdc': 'usdc',
    'bnb': 'bnb', 'xrp': 'xrp',
    'trx': 'trx', 'tron': 'trx'
}

NEON_ICONS_CONFIG = [
    {'id': 'bull', 'label': '上漲 Bull', 'icon': 'trending-up', 'color': 'text-green-400', 'bg': 'bg-green-400'},
    {'id': 'bear', 'label': '下跌 Bear', 'icon': 'trending-down', 'color': 'text-red-400', 'bg': 'bg-red-400'},
    {'id': 'alert', 'label': '警告 Alert', 'icon': 'alert-triangle', 'color': 'text-yellow-400', 'bg': 'bg-yellow-400'},
    {'id': 'lock', 'label': '鎖倉 Lock', 'icon': 'lock', 'color': 'text-purple-400', 'bg': 'bg-purple-400'},
    {'id': 'unlock', 'label': '解鎖 Unlock', 'icon': 'unlock', 'color': 'text-pink-400', 'bg': 'bg-pink-400'},
    {'id': 'tech', 'label': '技術 Tech', 'icon': 'cpu', 'color': 'text-blue-400', 'bg': 'bg-blue-400'},
    {'id': 'swap', 'label': '交易 Swap', 'icon': 'arrow-right-left', 'color': 'text-indigo-400', 'bg': 'bg-indigo-400'},
    {'id': 'news', 'label': '公告 News', 'icon': 'megaphone', 'color': 'text-orange-400', 'bg': 'bg-orange-400'},
    {'id': 'fund', 'label': '資金 Fund', 'icon': 'dollar-sign', 'color': 'text-emerald-400', 'bg': 'bg-emerald-400'},
    {'id': 'event', 'label': '活動 Event', 'icon': 'zap', 'color': 'text-yellow-300', 'bg': 'bg-yellow-300'},
]

# === 工具函式 ===

def remove_white_background_logic(image: Image.Image) -> Image.Image:
    image = image.convert("RGBA")
    data = np.array(image)
    r, g, b, a = data.T
    white_areas = (r > 240) & (g > 240) & (b > 240)
    data[..., 3][white_areas.T] = 0
    return Image.fromarray(data)

def image_to_base64(image: Image.Image) -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffered.getvalue()).decode()}"

def fetch_coingecko_image(query):
    try:
        url = f"https://api.coingecko.com/api/v3/search?query={query}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        if data.get('coins') and len(data['coins']) > 0:
            best_match = data['coins'][0]
            image_url = best_match.get('large') or best_match.get('thumb')
            if image_url:
                img_resp = requests.get(image_url, headers=headers, timeout=5)
                img = Image.open(io.BytesIO(img_resp.content))
                return img, best_match.get('name')
        return None, None
    except Exception as e:
        print(f"Error fetching from CoinGecko: {e}")
        return None, None

def get_default_token_image(symbol):
    url = f"https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/{symbol.lower()}.png"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except:
        pass
    return None

# === 初始化 Session State ===
if 'news_data' not in st.session_state:
    st.session_state.news_data = [
        {
            "id": 1,
            "title": "HYPE 正式解鎖！",
            "content": "3.12 億美元代幣已進入流通，現貨與合約交易全面開啟。",
            "token_mode": "custom",
            "token_value": "HYPE", 
            "token_image_base64": None, 
            "status_mode": "auto",
            "status_value": None
        },
        {
            "id": 2,
            "title": "Solana 週末持續霸榜！",
            "content": "週末效應加持，鏈上交易熱度不減，DEX 依然穩居活躍榜首。",
            "token_mode": "auto",
            "token_value": None,
            "token_image_base64": None,
            "status_mode": "auto",
            "status_value": None
        },
        {
            "id": 3,
            "title": "Uniswap 跨鏈功能開通！",
            "content": "Monad 主網跨鏈兌換正式上線 (Live)，體驗全新生態流動性。",
            "token_mode": "auto",
            "token_value": None,
            "token_image_base64": None,
            "status_mode": "auto",
            "status_value": None
        },
        {
            "id": 4,
            "title": "週末行情波動提醒！",
            "content": "週末流動性變化較大，請留意交易滑點與市場風險。",
            "token_mode": "none",
            "token_value": None,
            "token_image_base64": None,
            "status_mode": "select",
            "status_value": "alert"
        }
    ]

if 'global_settings' not in st.session_state:
    st.session_state.global_settings = {
        "main_title": "DEX 速報",
        "sub_title": "社群小編獨家整理",
        "date": datetime.datetime.now().strftime("%m/%d"),
        "footer_text": FOOTER_PRESETS[0],
        "logo_base64": None # 新增：用於儲存上傳的 Logo
    }

# === 介面邏輯 ===

st.title("⚡ 霓虹新聞速報產生器 (Streamlit 版)")
st.markdown("### 1. 全域設定")

# 上傳 Logo 的區塊
uploaded_logo = st.file_uploader("上傳左上角 Logo (若上傳則會取代「主標題」文字)", type=['png', 'jpg', 'jpeg', 'svg'])
if uploaded_logo:
    logo_img = Image.open(uploaded_logo)
    # 不強制去背，因為 Logo 可能需要保留背景，或使用者已經處理好了
    st.session_state.global_settings['logo_base64'] = image_to_base64(logo_img)
else:
    st.session_state.global_settings['logo_base64'] = None

col1, col2, col3 = st.columns([2, 1, 2])
with col1:
    # 只有在沒有上傳 Logo 時，這個輸入框才會有作用（視覺上提示使用者）
    if st.session_state.global_settings['logo_base64']:
        st.info("已上傳 Logo，主標題文字將被隱藏。")
        st.session_state.global_settings['main_title'] = st.text_input("主標題 (目前被 Logo 取代)", st.session_state.global_settings['main_title'], disabled=True)
    else:
        st.session_state.global_settings['main_title'] = st.text_input("主標題 (如：DEX 速報)", st.session_state.global_settings['main_title'])

with col2:
    st.session_state.global_settings['date'] = st.text_input("日期", st.session_state.global_settings['date'])
with col3:
    st.session_state.global_settings['sub_title'] = st.text_input("副標題", st.session_state.global_settings['sub_title'])

st.markdown("---")
st.markdown("### 2. 新聞卡片編輯")

for idx, item in enumerate(st.session_state.news_data):
    with st.expander(f"新聞卡片 #{idx+1} - {item['title']}", expanded=False):
        c1, c2 = st.columns([1, 1])
        
        with c1:
            new_title = st.text_input(f"標題 #{idx+1}", item['title'], key=f"title_{idx}")
            new_content = st.text_area(f"內文 #{idx+1}", item['content'], key=f"content_{idx}")
            st.session_state.news_data[idx]['title'] = new_title
            st.session_state.news_data[idx]['content'] = new_content
        
        with c2:
            st.caption("代幣圖片設定 (Token)")
            token_mode = st.selectbox("模式", ["auto", "custom_search", "upload", "none"], key=f"t_mode_{idx}", index=["auto", "custom_search", "upload", "none"].index(item['token_mode'] if item['token_mode'] in ["auto", "custom_search", "upload", "none"] else "auto"))
            st.session_state.news_data[idx]['token_mode'] = token_mode
            current_img_b64 = st.session_state.news_data[idx]['token_image_base64']

            if token_mode == "auto":
                found_token = None
                search_text = (new_title + new_content).lower()
                for key, symbol in TOKEN_MAPPING.items():
                    if key in search_text:
                        found_token = symbol
                        break
                if found_token:
                    st.info(f"偵測到: {found_token.upper()}")
                    if not current_img_b64:
                        pil_img = get_default_token_image(found_token)
                        if pil_img:
                             st.session_state.news_data[idx]['token_image_base64'] = image_to_base64(pil_img)
                else:
                    st.warning("未自動偵測到代幣關鍵字")
            
            elif token_mode == "custom_search":
                search_query = st.text_input("輸入代幣名稱 (CoinGecko)", key=f"search_{idx}")
                if st.button("搜尋並去背", key=f"btn_search_{idx}") and search_query:
                    with st.spinner("搜尋中..."):
                        img, name = fetch_coingecko_image(search_query)
                        if img:
                            img = remove_white_background_logic(img)
                            st.session_state.news_data[idx]['token_image_base64'] = image_to_base64(img)
                            st.success(f"已載入: {name}")
                        else:
                            st.error("找不到代幣")

            elif token_mode == "upload":
                uploaded_file = st.file_uploader("上傳圖片", type=['png', 'jpg', 'jpeg'], key=f"up_{idx}")
                if uploaded_file:
                    img = Image.open(uploaded_file)
                    if st.checkbox("自動去除白色背景", value=True, key=f"rmbg_{idx}"):
                        img = remove_white_background_logic(img)
                    st.session_state.news_data[idx]['token_image_base64'] = image_to_base64(img)

            if st.session_state.news_data[idx]['token_image_base64']:
                st.image(st.session_state.news_data[idx]['token_image_base64'], width=64)
                if st.button("清除圖片", key=f"clr_{idx}"):
                     st.session_state.news_data[idx]['token_image_base64'] = None

            st.caption("狀態圖示 (Status)")
            status_options = ["auto", "none"] + [i['id'] for i in NEON_ICONS_CONFIG]
            current_status = item['status_mode'] if item['status_mode'] in ["auto", "none"] else item['status_value']
            
            display_index = 0
            if item['status_mode'] == 'select' and item['status_value'] in [i['id'] for i in NEON_ICONS_CONFIG]:
                 current_status = item['status_value']
            
            if current_status in status_options:
                 display_index = status_options.index(current_status)

            selected_status = st.selectbox("選擇狀態", status_options, index=display_index, key=f"st_{idx}", format_func=lambda x: next((i['label'] for i in NEON_ICONS_CONFIG if i['id'] == x), x))

            if selected_status in ["auto", "none"]:
                st.session_state.news_data[idx]['status_mode'] = selected_status
                st.session_state.news_data[idx]['status_value'] = None
            else:
                st.session_state.news_data[idx]['status_mode'] = "select"
                st.session_state.news_data[idx]['status_value'] = selected_status

st.markdown("---")
st.markdown("### 3. 底部跑馬燈 (Footer)")

footer_choice = st.selectbox("選擇常用金句", ["自訂"] + FOOTER_PRESETS)
if footer_choice == "自訂":
    final_footer = st.text_input("輸入自訂文字", st.session_state.global_settings['footer_text'])
else:
    final_footer = footer_choice
st.session_state.global_settings['footer_text'] = final_footer

# === HTML 生成核心 ===
def generate_html_preview():
    news_items_html = ""
    
    for idx, item in enumerate(st.session_state.news_data):
        token_html = ""
        has_token = False
        if item['token_mode'] != 'none' and item['token_image_base64']:
            has_token = True
            token_html = f"""
            <div class="relative w-20 h-20">
                <img src="{item['token_image_base64']}" class="w-full h-full object-contain drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]" />
            </div>
            """
        
        status_config = None
        detected_status_id = 'activity' 
        text_content = (item['title'] + item['content']).lower()
        
        if item['status_mode'] == 'select' and item['status_value']:
             status_id = item['status_value']
             status_config = next((i for i in NEON_ICONS_CONFIG if i['id'] == status_id), None)
        elif item['status_mode'] == 'auto':
             if has_token:
                 status_config = None 
             else:
                 if any(k in text_content for k in ['上漲', '新高', 'bull']): detected_status_id = 'bull'
                 elif any(k in text_content for k in ['下跌', '暴跌', 'bear']): detected_status_id = 'bear'
                 elif any(k in text_content for k in ['警告', '風險', 'alert']): detected_status_id = 'alert'
                 status_config = next((i for i in NEON_ICONS_CONFIG if i['id'] == detected_status_id), None)
        
        status_html = ""
        title_color_class = "text-white"
        
        if status_config:
            title_color_class = status_config['color'] 
            status_html = f"""
            <div class="relative flex items-center justify-center w-20 h-20">
                <div class="absolute inset-0 blur-xl opacity-30 {status_config['bg']}"></div>
                <i data-lucide="{status_config['icon']}" class="w-full h-full {status_config['color']}" stroke-width="1.5"></i>
            </div>
            """
        elif has_token:
            title_color_class = "text-green-300"
            
        border_colors = [
            "border-green-500/30 shadow-[0_0_15px_rgba(74,222,128,0.15)]",
            "border-purple-500/30 shadow-[0_0_15px_rgba(168,85,247,0.15)]",
            "border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.15)]",
            "border-yellow-500/30 shadow-[0_0_15px_rgba(234,179,8,0.15)]"
        ]
        border_class = border_colors[idx % len(border_colors)]
        title_style = f'class="text-3xl font-bold leading-tight mb-4 {title_color_class}"'

        news_items_html += f"""
        <div class="relative bg-gray-900/80 rounded-2xl p-6 border {border_class} flex flex-col justify-between h-[280px] backdrop-blur-sm">
            <div class="relative z-10">
                <h3 {title_style}>{item['title']}</h3>
                <p class="text-gray-300 text-xl leading-relaxed font-medium">{item['content']}</p>
            </div>
            <div class="absolute bottom-4 right-4 z-0">
                <div class="flex items-end gap-3">
                    {token_html}
                    {status_html}
                </div>
            </div>
        </div>
        """

    # 處理標題區域：如果有上傳 Logo，就顯示 Logo；否則顯示文字標題
    logo_or_title_html = ""
    if st.session_state.global_settings['logo_base64']:
        logo_or_title_html = f"""
        <img src="{st.session_state.global_settings['logo_base64']}" class="h-14 object-contain mr-4" />
        <span class="text-white text-3xl font-bold">{st.session_state.global_settings['date']}</span>
        """
    else:
        logo_or_title_html = f"""
        <h1 class="text-4xl font-black text-green-400 tracking-tight">
            {st.session_state.global_settings['main_title']} 
            <span class="text-white ml-2 text-3xl font-bold">{st.session_state.global_settings['date']}</span>
        </h1>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/lucide@latest"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Noto Sans TC', sans-serif; background: transparent; }}
        </style>
    </head>
    <body class="flex flex-col items-center justify-center min-h-screen py-10 gap-6">
        
        <div class="flex gap-4">
             <button onclick="downloadImage()" class="flex items-center gap-2 bg-green-500 hover:bg-green-600 text-black font-bold py-2 px-6 rounded-full shadow-lg transition-transform hover:scale-105 cursor-pointer">
                <i data-lucide="download"></i>
                下載圖片 (PNG)
            </button>
        </div>

        <div id="capture-wrapper" class="p-2">
            <div id="capture-area" class="w-[800px] bg-black px-8 pt-8 pb-12 shadow-[0_0_50px_rgba(0,0,0,0.8)] overflow-visible relative">
                <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-green-400 via-purple-500 to-pink-500"></div>
                
                <!-- Header 區域更新 -->
                <div class="flex items-end justify-between mb-6 pb-4 border-b border-gray-800">
                    <div class="flex items-center gap-4">
                        {logo_or_title_html}
                        <div class="h-6 w-[1px] bg-gray-600"></div>
                        <h2 class="text-xl text-white font-medium tracking-wide">
                            {st.session_state.global_settings['sub_title']}
                        </h2>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                    {news_items_html}
                </div>

                <div class="mt-6 pt-4 border-t border-gray-800">
                    <div class="flex items-start gap-2 mb-2">
                        <span class="text-green-400 font-bold text-lg whitespace-nowrap mt-0.5">One More Thing:</span>
                        <p class="text-white text-lg font-medium break-words leading-relaxed">{st.session_state.global_settings['footer_text']}</p>
                    </div>
                    <div class="flex justify-between items-center mt-4 text-gray-500 text-sm">
                        <div class="flex items-center gap-2">
                            <div class="bg-white text-black font-black px-2 py-0.5 text-xs rounded-sm">APP</div>
                            <span class="font-bold tracking-widest text-white">GENERATOR</span>
                        </div>
                        <p class="mx-4">以上內容不構成任何投資建議，投資有風險，入市需謹慎。</p>
                        <div class="flex gap-2">
                            <i data-lucide="globe" size="16"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            lucide.createIcons();

            function downloadImage() {{
                const element = document.getElementById('capture-area');
                const btn = document.querySelector('button');
                const originalText = btn.innerHTML;
                btn.innerText = "生成中...";
                
                html2canvas(element, {{
                    useCORS: true,
                    scale: 2,
                    backgroundColor: "#000000",
                    height: element.scrollHeight + 10,
                    scrollY: 0,
                    windowHeight: element.scrollHeight + 100
                }}).then(canvas => {{
                    const link = document.createElement('a');
                    link.download = 'neon-news-{st.session_state.global_settings["date"].replace("/", "")}.png';
                    link.href = canvas.toDataURL('image/png');
                    link.click();
                    btn.innerHTML = originalText;
                }}).catch(err => {{
                    console.error("截圖失敗:", err);
                    alert("圖片生成失敗，請檢查瀏覽器主控台。");
                    btn.innerHTML = originalText;
                }});
            }}
        </script>
    </body>
    </html>
    """
    return html_content

st.markdown("### 4. 即時預覽")
st.info("💡 說明：若已上傳 Logo，預覽區左上角會顯示您的圖片；若無上傳則顯示文字標題。")

preview_html = generate_html_preview()
st.components.v1.html(preview_html, height=1000, scrolling=True)


