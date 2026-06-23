import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
font_path = 'simhei.ttc'
if os.path.exists(font_path):
    fm.fontManager.addfont(font_path)
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
else:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
import seaborn as sns
from sklearn.cluster import KMeans
import datetime
import matplotlib.font_manager as fm
import re
from collections import Counter

# ==========================================
# 1. 基础设置与中文字体配置
# ==========================================
st.set_page_config(page_title="Inventory and Insight System", layout="wide")

@st.cache_resource
def setup_fonts():
    font_paths = [
        r"C:\Windows\Fonts\msyh.ttc", 
        r"C:\Windows\Fonts\simhei.ttf", 
        r"C:\Windows\Fonts\simsun.ttc", 
        r"/System/Library/Fonts/PingFang.ttc"
    ]
    for path in font_paths:
        if os.path.exists(path):
            fm.fontManager.addfont(path)
            plt.rcParams['font.family'] = fm.FontProperties(fname=path).get_name()
            break
    plt.rcParams['axes.unicode_minus'] = False

setup_fonts()

DB_FILE = "public_survey_data.csv"
CRED_FILE = "merchant_accounts.csv"

def init_credentials():
    if not os.path.exists(CRED_FILE):
        df = pd.DataFrame([{"username": "Iammerchant", "password": "letus888", "category": "时装"}])
        df.to_csv(CRED_FILE, index=False, encoding='utf-8-sig')

init_credentials()

# ==========================================
# 2. 状态管理、语言翻译与全国省市字典
# ==========================================
if 'language' not in st.session_state: 
    st.session_state.language = None
if 'page' not in st.session_state: 
    st.session_state.page = 'lang_select'
if 'merchant_category' not in st.session_state: 
    st.session_state.merchant_category = ''
if 'public_interest' not in st.session_state: 
    st.session_state.public_interest = ''

# 完整 34 个省级行政区字典
# 完整 34 个省级行政区及下辖所有地级市/自治州字典
REGION_DICT = {
    "北京": ["北京市"],
    "天津": ["天津市"],
    "上海": ["上海市"],
    "重庆": ["重庆市"],
    "河北": ["石家庄市", "唐山市", "秦皇岛市", "邯郸市", "邢台市", "保定市", "张家口市", "承德市", "沧州市", "廊坊市", "衡水市"],
    "山西": ["太原市", "大同市", "阳泉市", "长治市", "晋城市", "朔州市", "晋中市", "运城市", "忻州市", "临汾市", "吕梁市"],
    "内蒙古": ["呼和浩特市", "包头市", "乌海市", "赤峰市", "通辽市", "鄂尔多斯市", "呼伦贝尔市", "巴彦淖尔市", "乌兰察布市", "兴安盟", "锡林郭勒盟", "阿拉善盟"],
    "辽宁": ["沈阳市", "大连市", "鞍山市", "抚顺市", "本溪市", "丹东市", "锦州市", "营口市", "阜新市", "辽阳市", "盘锦市", "铁岭市", "朝阳市", "葫芦岛市"],
    "吉林": ["长春市", "吉林市", "四平市", "辽源市", "通化市", "白山市", "松原市", "白城市", "延边朝鲜族自治州"],
    "黑龙江": ["哈尔滨市", "齐齐哈尔市", "鸡西市", "鹤岗市", "双鸭山市", "大庆市", "伊春市", "佳木斯市", "七台河市", "牡丹江市", "黑河市", "绥化市", "大兴安岭地区"],
    "江苏": ["南京市", "无锡市", "徐州市", "常州市", "苏州市", "南通市", "连云港市", "淮安市", "盐城市", "扬州市", "镇江市", "泰州市", "宿迁市"],
    "浙江": ["杭州市", "宁波市", "温州市", "嘉兴市", "湖州市", "绍兴市", "金华市", "衢州市", "舟山市", "台州市", "丽水市"],
    "安徽": ["合肥市", "芜湖市", "蚌埠市", "淮南市", "马鞍山市", "淮北市", "铜陵市", "安庆市", "黄山市", "滁州市", "阜阳市", "宿州市", "六安市", "亳州市", "池州市", "宣城市"],
    "福建": ["福州市", "厦门市", "莆田市", "三明市", "泉州市", "漳州市", "南平市", "龙岩市", "宁德市"],
    "江西": ["南昌市", "景德镇市", "萍乡市", "九江市", "新余市", "鹰潭市", "赣州市", "吉安市", "宜春市", "抚州市", "上饶市"],
    "山东": ["济南市", "青岛市", "淄博市", "枣庄市", "东营市", "烟台市", "潍坊市", "济宁市", "泰安市", "威海市", "日照市", "临沂市", "德州市", "聊城市", "滨州市", "菏泽市"],
    "河南": ["郑州市", "开封市", "洛阳市", "平顶山市", "安阳市", "鹤壁市", "新乡市", "焦作市", "濮阳市", "许昌市", "漯河市", "三门峡市", "南阳市", "商丘市", "信阳市", "周口市", "驻马店市", "济源市"],
    "湖北": ["武汉市", "黄石市", "十堰市", "宜昌市", "襄阳市", "鄂州市", "荆门市", "孝感市", "荆州市", "黄冈市", "咸宁市", "随州市", "恩施土家族苗族自治州", "仙桃市", "潜江市", "天门市", "神农架林区"],
    "湖南": ["长沙市", "株洲市", "湘潭市", "衡阳市", "邵阳市", "岳阳市", "常德市", "张家界市", "益阳市", "郴州市", "永州市", "怀化市", "娄底市", "湘西土家族苗族自治州"],
    "广东": ["广州市", "深圳市", "珠海市", "汕头市", "佛山市", "韶关市", "湛江市", "肇庆市", "江门市", "茂名市", "惠州市", "梅州市", "汕尾市", "河源市", "阳江市", "清远市", "东莞市", "中山市", "潮州市", "揭阳市", "云浮市"],
    "广西": ["南宁市", "柳州市", "桂林市", "梧州市", "北海市", "防城港市", "钦州市", "贵港市", "玉林市", "百色市", "贺州市", "河池市", "来宾市", "崇左市"],
    "海南": ["海口市", "三亚市", "三沙市", "儋州市", "五指山市", "琼海市", "文昌市", "万宁市", "东方市", "定安县", "屯昌县", "澄迈县", "临高县", "白沙黎族自治县", "昌江黎族自治县", "乐东黎族自治县", "陵水黎族自治县", "保亭黎族苗族自治县", "琼中黎族苗族自治县"],
    "四川": ["成都市", "自贡市", "攀枝花市", "泸州市", "德阳市", "绵阳市", "广元市", "遂宁市", "内江市", "乐山市", "南充市", "眉山市", "宜宾市", "广安市", "达州市", "雅安市", "巴中市", "资阳市", "阿坝藏族羌族自治州", "甘孜藏族自治州", "凉山彝族自治州"],
    "贵州": ["贵阳市", "六盘水市", "遵义市", "安顺市", "毕节市", "铜仁市", "黔西南布依族苗族自治州", "黔东南苗族侗族自治州", "黔南布依族苗族自治州"],
    "云南": ["昆明市", "曲靖市", "玉溪市", "保山市", "昭通市", "丽江市", "普洱市", "临沧市", "楚雄彝族自治州", "红河哈尼族彝族自治州", "文山壮族苗族自治州", "西双版纳傣族自治州", "大理白族自治州", "德宏傣族景颇族自治州", "怒江傈僳族自治州", "迪庆藏族自治州"],
    "西藏": ["拉萨市", "日喀则市", "昌都市", "林芝市", "山南市", "那曲市", "阿里地区"],
    "陕西": ["西安市", "铜川市", "宝鸡市", "咸阳市", "渭南市", "延安市", "汉中市", "榆林市", "安康市", "商洛市"],
    "甘肃": ["兰州市", "嘉峪关市", "金昌市", "白银市", "天水市", "武威市", "张掖市", "平凉市", "酒泉市", "庆阳市", "定西市", "陇南市", "临夏回族自治州", "甘南藏族自治州"],
    "青海": ["西宁市", "海东市", "海北藏族自治州", "黄南藏族自治州", "海南藏族自治州", "果洛藏族自治州", "玉树藏族自治州", "海西蒙古族藏族自治州"],
    "宁夏": ["银川市", "石嘴山市", "吴忠市", "固原市", "中卫市"],
    "新疆": ["乌鲁木齐市", "克拉玛依市", "吐鲁番市", "哈密市", "昌吉回族自治州", "博尔塔拉蒙古自治州", "巴音郭楞蒙古自治州", "阿克苏地区", "克孜勒苏柯尔克孜自治州", "喀什地区", "和田地区", "伊犁哈萨克自治州", "塔城地区", "阿勒泰地区", "石河子市", "阿拉尔市", "图木舒克市", "五家渠市"],
    "中国香港": ["香港岛", "九龙", "新界"],
    "中国澳门": ["澳门半岛", "氹仔", "路环"],
    "中国台湾": ["台北市", "新北市", "桃园市", "台中市", "台南市", "高雄市", "基隆市", "新竹市", "嘉义市"]
}

def switch_page(page_name): 
    st.session_state.page = page_name
    st.rerun()

def t(zh, en):
    return zh if st.session_state.get('language', 'zh') == 'zh' else en

def to_zh(val):
    if not isinstance(val, str): return val
    mapping = {
        "Female": "女", "Male": "男", "Lipstick": "口红", "Fashion": "时装",
        "Pink": "粉色", "Milk Tea": "奶茶色", "Rose": "玫瑰色", "Bean Paste": "豆沙色", "Red": "红色", "Orange": "橘色", "Chocolate": "巧克力色",
        "T-Shirt": "T恤", "New Arrivals": "当季新品", "Accessories": "配件", "Sweater": "毛衣", "Jeans": "牛仔裤", "Skirt": "裙子", "Socks": "袜子", "Sports": "运动",
        "Can": "能", "Cannot": "不能", "Not sure": "不确定",
        "No suggestions for now": "暂无建议", "Have specific suggestions": "有具体建议",
        "1 Week": "一个星期", "1 Month": "一个月", "3 Months": "三个月", "6 Months": "六个月", "1 Year": "一年"
    }
    return mapping.get(val, val)

# ==========================================
# 3. 数据读取与智能NLP分析引擎
# ==========================================
@st.cache_data
def load_uploaded_data(file):
    if file.name.endswith('.csv'):
        for enc in ['utf-8', 'gbk', 'gb18030']:
            try:
                file.seek(0)
                return pd.read_csv(file, encoding=enc)
            except: 
                continue
        file.seek(0)
        return pd.read_csv(file, encoding='utf-8', errors='ignore')
    else:
        return pd.read_excel(file)

@st.cache_data(ttl=60)
def load_survey_data(db_file):
    if not os.path.exists(db_file): 
        return pd.DataFrame()
    return pd.read_csv(db_file)

@st.cache_data
def run_kmeans_clustering(_df_model, col_qty, col_sales):
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    return kmeans.fit_predict(_df_model[[col_qty, col_sales]]).astype(str)

def analyze_sentiment(text):
    if not isinstance(text, str) or not text.strip(): 
        return "⚪ 中立 (Neutral)"
        
    pos_words = ['好', '赞', '喜欢', '不错', '棒', '满意', '多', '快', '😊', '😍', '👍', 'good', 'great', 'excellent', 'love', 'nice', 'best']
    neg_words = ['差', '糟', '贵', '慢', '不', '少', '退', '😡', '😞', '👎', '😭', 'bad', 'terrible', 'worst', 'too', 'expensive', 'slow']
    
    pos_score = 0
    neg_score = 0

    text_lower = text.lower()
    for w in pos_words:
        pos_score += text_lower.count(w)
    for w in neg_words:
        neg_score += text_lower.count(w)

    if '?' in text or '？' in text:
        neg_score += 1
        
    exclamation = text.count('!') + text.count('！')
    if exclamation > 0:
        if pos_score > neg_score: pos_score += exclamation
        elif neg_score > pos_score: neg_score += exclamation
        else: neg_score += 1 

    all_caps_words = re.findall(r'\b[A-Z]{2,}\b', text)
    for cap_word in all_caps_words:
        cw_lower = cap_word.lower()
        if any(pw in cw_lower for pw in pos_words):
            pos_score += 2  
        elif any(nw in cw_lower for nw in neg_words):
            neg_score += 2  

    if pos_score > neg_score: return "🟢 好评 (Positive)"
    elif neg_score > pos_score: return "🔴 差评 (Negative)"
    else: return "⚪ 中立 (Neutral)"

import jieba

def extract_keywords(text_list, top_n=10):
    words = []
    # 扩展了停用词库，过滤掉更多无意义的词
    stop_words = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '建议', '希望', '可以', '觉得', '还是', '比较', '太', '非常', '有些', '有点', '应该', '需要'}
    
    for text in text_list:
        if not isinstance(text, str): continue
        
        # 1. 提取英文单词 (例如 "T-shirt", "bug")
        eng_words = re.findall(r'[a-zA-Z]+', text)
        words.extend([w.lower() for w in eng_words if len(w) > 2])
        
        # 2. 提取纯中文进行智能分词
        cn_text = re.sub(r'[^\u4e00-\u9fa5]', '', text)
        if cn_text:
            # 使用 jieba 进行精确模式分词
            seg_list = jieba.cut(cn_text)
            for w in seg_list:
                # 只保留长度大于等于2的词，且不在停用词表中
                if len(w) >= 2 and w not in stop_words:
                    words.append(w)
                    
    return Counter(words).most_common(top_n)

# ==========================================
# 4. 页面渲染函数 基础页面与公众入口
# ==========================================
def page_lang_select():
    st.markdown("<h1 style='text-align: center; margin-top: 10vh;'>🌐 Please Select Your Language / 请选择语言</h1>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    with col2:
        if st.button("中文Chinese", use_container_width=True):
            st.session_state.language = 'zh'
            switch_page('home')
    with col3:
        if st.button("English", use_container_width=True):
            st.session_state.language = 'en'
            switch_page('home')

def page_home():
    col_space, col_lang = st.columns([8, 2])
    with col_lang:
        if st.button("🌐 " + t("切换语言", "Change Language"), use_container_width=True): 
            switch_page('lang_select')
            
    st.title(t("🛍️ 零售库存优化与客户需求洞察平台", "🛍️ Retail Inventory Optimization and Customer Insight Platform"))
    st.markdown("---")
    st.write(t("请选择您的身份进入系统：", "Please select your role to enter:"))
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button(t("🏢 商家入口", "🏢 Merchant Portal"), use_container_width=True): 
            switch_page('merchant_login')
    with col2:
        if st.button(t("👥 公众入口", "👥 Public Portal"), use_container_width=True): 
            switch_page('public_info')
    with col3:
        if st.button(t("⚙️ 技术支持", "⚙️ Tech Portal"), use_container_width=True): 
            switch_page('tech_portal')

import urllib.parse
import pandas as pd
import os
import streamlit as st

# ⚠️ 这里已经改成了 page_tech_portal，和你的 main 函数保持一致了
def page_tech_portal():
    st.title(t("⚙️ 技术支持与联系我们", "⚙️ Tech Support & Contact Us"))
    if st.button(t("返回首页", "Back to Home")):
        switch_page('home')
        st.rerun()

    st.write("---")
    
    # 使用 Tabs 将页面分为“商家入口”和“公众入口”
    tab_merchant_title = t("🧑‍💼 商家专属入口", "🧑‍💼 Merchant Portal")
    tab_public_title = t("🌍 公众联系入口", "🌍 Public Contact Portal")
    tab_merchant, tab_public = st.tabs([tab_merchant_title, tab_public_title])
    
    # ==========================================
    # 标签页 1：商家专属入口
    # ==========================================
    with tab_merchant:
        st.subheader(t("商家身份验证", "Merchant Authentication"))

        if 'support_logged_in' not in st.session_state:
            st.session_state.support_logged_in = False
            st.session_state.support_user = ""

        if not st.session_state.support_logged_in:
            user_str = st.text_input(t("请输入商家用户名", "Enter Merchant Username"), key="support_user_input")
            pwd_str = st.text_input(t("请输入密码", "Enter Password"), type="password", key="support_pwd_input")
            
            if st.button(t("验证身份", "Verify Identity")):
                if os.path.exists(CRED_FILE):
                    df = pd.read_csv(CRED_FILE)
                    df['username'] = df['username'].astype(str)
                    df['password'] = df['password'].astype(str)
                    
                    user_row = df[(df['username'] == str(user_str)) & (df['password'] == str(pwd_str))]
                    if not user_row.empty:
                        st.session_state.support_logged_in = True
                        st.session_state.support_user = str(user_str)
                        st.success(t("验证成功！请填写下方的支持表单。", "Verification successful! Please fill out the support form below."))
                        st.rerun()
                    else:
                        st.error(t("用户名或密码错误，请重试！", "Incorrect username or password, please try again!"))
                else:
                    st.error(t("系统暂无商家数据。", "No merchant data in the system."))

        if st.session_state.support_logged_in:
            st.write(f"{t('当前登录账号：', 'Current logged-in account: ')}**{st.session_state.support_user}**")
            
            st.markdown(f"#### {t('提交支持工单', 'Submit Support Ticket')}")

            opt_config = t("修改配置", "Modify Configuration")
            opt_bug = t("报告 Bug", "Report Bug")

            options = st.multiselect(
                t("请选择您需要的服务", "Please select the services you need"),
                [opt_config, opt_bug]
            )
            
            config_text = ""
            bug_text = ""
            phone = ""

            if opt_config in options:
                config_text = st.text_area(t("🔧 请详细描述您需要修改的配置内容：", "🔧 Please describe the configuration changes you need in detail:"))
                
            if opt_bug in options:
                bug_text = st.text_area(t("🐛 请详细描述您遇到的 Bug：", "🐛 Please describe the Bug you encountered in detail:"))
                phone = st.text_input(t("📞 您的联系电话", "📞 Your Contact Number"))

            if st.button(t("生成并发送邮件", "Generate and Send Email"), key="btn_send_merchant"):

                if len(options) == 0:
                    st.error(t("请至少选择一项服务！", "Please select at least one service!"))
                elif opt_bug in options and phone.strip() == "":
                    st.error(t("报告 Bug 时，必须填写联系电话以便我们与您联系！", "When reporting a Bug, a contact number is required so we can reach you!"))
                elif opt_config in options and config_text.strip() == "" and opt_bug not in options:
                    st.error(t("请填写修改配置的具体内容！", "Please fill in the specific details for the configuration modification!"))
                elif opt_bug in options and bug_text.strip() == "" and opt_config not in options:
                    st.error(t("请填写 Bug 的具体描述！", "Please fill in the specific description of the Bug!"))
                else:

                    subject = f"{t('【系统工单】来自商家', '[System Ticket] Tech Support Request from Merchant')} {st.session_state.support_user}"
                    body = f"{t('商家账号:', 'Merchant Account:')} {st.session_state.support_user}\n\n"
                    if opt_config in options:
                        body += f"{t('【修改配置需求】', '[Configuration Modification Request]')}\n{config_text}\n\n"
                    if opt_bug in options:
                        body += f"{t('【Bug 报告】', '[Bug Report]')}\n{bug_text}\n"
                        body += f"{t('联系电话:', 'Contact Number:')} {phone}\n\n"

                    subject_encoded = urllib.parse.quote(subject)
                    body_encoded = urllib.parse.quote(body)
                    mailto_url = f"mailto:23D011@hksyu.edu.hk?subject={subject_encoded}&body={body_encoded}"
                    st.markdown(f'<meta http-equiv="refresh" content="0; url={mailto_url}">', unsafe_allow_html=True)
                    st.success(t("✅ 正在唤起您的邮箱客户端，请在弹出的界面中点击发送！", "✅ Launching your email client, please click send in the pop-up window!"))

    # ==========================================
    # 标签页 2：公众联系入口
    # ==========================================
    with tab_public:
        st.subheader(t("公众意见与反馈", "Public Opinion & Feedback"))
        st.info(t("欢迎您为我们的系统提供宝贵的意见。点击下方按钮，将直接通过您的邮箱与我们的开发者取得联系。", "Welcome to provide valuable feedback for our system. Click the button below to contact our developers directly via your email."))
        
        public_msg = st.text_area(t("📝 请填写您的留言或反馈内容：", "📝 Please enter your message or feedback:"), height=150)
        
        if st.button(t("生成并发送邮件", "Generate and Send Email"), key="btn_send_public"):
            if public_msg.strip() == "":
                st.error(t("请先填写留言内容！", "Please fill in the message content first!"))
            else:
                subject = t("【公众反馈】系统意见与建议", "[Public Feedback] System Opinions and Suggestions")
                body = f"{t('【反馈内容】', '[Feedback Content]')}\n{public_msg}\n"

                subject_encoded = urllib.parse.quote(subject)
                body_encoded = urllib.parse.quote(body)
                mailto_url = f"mailto:23D011@hksyu.edu.hk?subject={subject_encoded}&body={body_encoded}"
                st.markdown(f'<meta http-equiv="refresh" content="0; url={mailto_url}">', unsafe_allow_html=True)
                st.success(t("✅ 正在唤起您的邮箱客户端，请在弹出的界面中点击发送！", "✅ Launching your email client, please click send in the pop-up window!"))

def page_merchant_login():
    st.title(t("商家登录 / 注册", "Merchant Login / Register"))
    login_mode = st.radio(t("请选择操作", "Select Action"), [t("🔑 登录", "🔑 Login"), t("📝 注册新账号", "📝 Register New Account")], horizontal=True)
    is_login = t("登录", "Login") in login_mode

    with st.form("merchant_login_form"):
        user = st.text_input(t("用户名", "Username"))
        pwd = st.text_input(t("密码", "Password"), type="password")
        if not is_login:
            cat = st.selectbox(t("经营类目", "Business Category"), [t("口红", "Lipstick"), t("时装", "Fashion")], index=None)
        else:
            cat = None
            
        col1, col2 = st.columns([1, 4])
        with col1:
            back = st.form_submit_button(t("返回", "Back"))
        with col2:
            btn_label = t("进入系统", "Enter System") if is_login else t("注册并进入", "Register & Enter")
            submitted = st.form_submit_button(btn_label)

    if back:
        switch_page('home')

    if submitted:
        if not user or not pwd:
            st.error(t("请填写账号和密码！", "Please fill in username and password!"))
        elif not is_login and not cat:
            st.error(t("请选择经营类目！", "Please select a business category!"))
        else:
            import os
            if not os.path.exists(CRED_FILE):
                pd.DataFrame(columns=['username', 'password', 'category']).to_csv(CRED_FILE, index=False)

            df = pd.read_csv(CRED_FILE)
            if 'category' not in df.columns:
                df['category'] = "未知类目"
                
            df['username'] = df['username'].astype(str)
            df['password'] = df['password'].astype(str)
            user_str, pwd_str = str(user), str(pwd)
            user_exists = user_str in df['username'].values

            if is_login:
                if user_exists:
                    user_row = df[(df['username'] == user_str) & (df['password'] == pwd_str)]
                    if not user_row.empty:
                        saved_cat = user_row.iloc[0]['category']
                        st.session_state.merchant_category = saved_cat
                        
                        st.success(t("登录成功！正在进入系统！", "Login successful! Entering system!"))
                        import time
                        time.sleep(1)
                        switch_page('merchant_dashboard')
                        st.rerun()
                    else:
                        st.error(t("密码错误！请重新输入！", "Incorrect Password! Please try again!"))
                else:
                    st.error(t("账号不存在，请先注册！", "Account does not exist, please register first!"))
            else:
                if user_exists:
                    st.error(t("账号已存在！请直接选择登录。", "Account already exists! Please choose Login."))
                else:
                    save_cat = to_zh(cat)
                    new_data = pd.DataFrame([{'username': user_str, 'password': pwd_str, 'category': save_cat}])
                    new_data.to_csv(CRED_FILE, mode='a', header=False, index=False, encoding='utf-8')
                    
                    st.session_state.merchant_category = save_cat
                    st.success(t("注册成功！正在进入系统！", "Registration successful! Entering system!"))
                    import time
                    time.sleep(1)
                    switch_page('merchant_dashboard')
                    st.rerun() 
                                                                               
def page_public_info():
    st.title(t("公众市场调研 - 基础信息", "Public Market Survey - Basic Info"))
    gender = st.selectbox(t("您的性别", "Your Gender"), [t("女", "Female"), t("男", "Male")], index=None)
    age = st.selectbox(t("您的年龄区间", "Age Range"), ["<18", "18-24", "25-31", "32-41", "42-52", ">52"], index=None)
    
    col_prov, col_city = st.columns(2)
    with col_prov: 
        prov = st.selectbox(t("所在省份", "Province"), list(REGION_DICT.keys()), index=None)
    with col_city: 
        city = st.selectbox(t("所在城市", "City"), REGION_DICT[prov] if prov else [], index=None)
        
    interest = st.selectbox(t("您最感兴趣的内容", "Most Interested Category"), [t("口红", "Lipstick"), t("时装", "Fashion")], index=None)
    
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 5])
    with col1: 
        if st.button(t("返回", "Back")): 
            switch_page('home')
    with col2: 
        if st.button(t("下一步", "Next Step")):
            if not all([gender, age, prov, city, interest]): 
                st.error(t("请完成所有选择！", "Please complete all selections!"))
            else:
                st.session_state.public_info = {"gender": to_zh(gender), "age": age, "prov": prov, "city": city, "interest": to_zh(interest)}
                st.session_state.public_interest = to_zh(interest)
                switch_page('public_survey')

def page_public_survey():
    st.title(t("公众市场调研 - 需求问卷", "Public Market Survey - Questionnaire"))
    interest = st.session_state.public_interest
    if interest == "口红":
        items = [t("粉色", "Pink"), t("奶茶色", "Milk Tea"), t("玫瑰色", "Rose"), t("豆沙色", "Bean Paste"), t("红色", "Red"), t("橘色", "Orange"), t("巧克力色", "Chocolate")]
    else:
        items = [t("T恤", "T-Shirt"), t("当季新品", "New Arrivals"), t("配件", "Accessories"), t("毛衣", "Sweater"), t("牛仔裤", "Jeans"), t("裙子", "Skirt"), t("袜子", "Socks"), t("运动", "Sports")]

    q1 = st.selectbox(t("1. 未来一个月您最希望购买的单品", "1. Most desired item next month"), items, index=None)
    q2 = st.selectbox(t("2. 期待价格", "2. Expected Price"), ["<100", "100-200", "200-300", ">300"], index=None)
    q3a = st.selectbox(t("3. 现阶段的内地品牌在您的城市的线下广告营销是否可以提高您的购买欲望？", "3. Can current offline advertising... increase your purchase desire?"), [t("能", "Can"), t("不能", "Cannot"), t("不确定", "Not sure")], index=None)
    q3b = st.selectbox(t("4. 现阶段的内地品牌在您的城市的线下服务是否可以提高您的购买欲望？", "4. Can current offline services... increase your purchase desire?"), [t("能", "Can"), t("不能", "Cannot"), t("不确定", "Not sure")], index=None)
    
    q5 = st.radio(t("5. 对门店与营销还有哪些具体建议？", "5. Specific suggestions for stores and marketing?"), [t("暂无建议", "No suggestions for now"), t("有具体建议", "Have specific suggestions")], index=None)
    
    sug_ad, sug_exp, sug_discount = "", "", ""
    if q5 == t("有具体建议", "Have specific suggestions"):
        sug_ad = st.text_input(t("📢 线下广告与推广建议:", "📢 Offline Advertising & Promotion:"))
        sug_exp = st.text_input(t("🛍️ 门店服务与体验期望:", "🛍️ Store Service & Experience:"))
        sug_discount = st.text_input(t("🎁 促销与活动期望:", "🎁 Promotion & Event Expectations:"))
        
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 5])
    with col1: 
        if st.button(t("返回", "Back")): 
            switch_page('public_info')
    with col2: 
        if st.button(t("提交问卷", "Submit")):
            if not all([q1, q2, q3a, q3b, q5]): 
                st.error(t("请完成所有选择题！", "Please complete all choices!"))
            elif q5 == t("有具体建议", "Have specific suggestions") and not (sug_ad or sug_exp or sug_discount): 
                st.error(t("请至少填写一项具体建议！", "Please fill in at least one specific suggestion!"))
            else:
                info = st.session_state.public_info
                data = {
                    "提交时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    "大类": info["interest"], "性别": info["gender"], "年龄": info["age"], 
                    "省份": info["prov"], "城市": info["city"], 
                    "期待单品": to_zh(q1), "期待价格": q2, 
                    "线下广告提高购买欲": to_zh(q3a), "线下服务提高购买欲": to_zh(q3b), 
                    "是否有建议": to_zh(q5), "建议_广告": sug_ad, "建议_感受": sug_exp, "建议_折扣": sug_discount
                }
                pd.DataFrame([data]).to_csv(DB_FILE, mode='a' if os.path.exists(DB_FILE) else 'w', header=not os.path.exists(DB_FILE), index=False, encoding='utf-8-sig')
                switch_page('public_thanks')

def page_public_thanks():
    st.markdown(f"<h1 style='text-align: center; color: #4CAF50; margin-top: 100px;'>{t('感谢您的提交！', 'Thank you for your submission!')}</h1>", unsafe_allow_html=True)
    if st.button(t("返回首页", "Back to Home"), use_container_width=True): 
        switch_page('home')

def page_merchant_dashboard():
    st.title(f"{t('商家控制台', 'Merchant Dashboard')} - {t(st.session_state.merchant_category, st.session_state.merchant_category)}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 " + t("现有数据分析", "Analyze Existing Data"), use_container_width=True): 
            switch_page('merchant_upload')
    with col2:
        if st.button("📈 " + t("查看公众结果", "View Public Results"), use_container_width=True): 
            switch_page('merchant_survey_filter')
            
    if st.button(t("退出登录", "Logout")): 
        switch_page('home')

def page_merchant_upload():
    st.title(t("现有数据分析引擎", "Data Analysis Engine"))
    if st.button(t("返回", "Back")): 
        switch_page('merchant_dashboard')
        
    uploaded_file = st.file_uploader(t("选择文件", "Select File"), type=['csv', 'xlsx'])
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        cols = list(load_uploaded_data(uploaded_file).columns)
        with st.form("upload_form"):
            c_sales = st.selectbox(t("销售金额列 【必填】", "Sales Column [Required]"), cols, index=None)
            c_date = st.selectbox(t("日期列 (可选)", "Date Column (Optional)"), cols, index=None)
            c_city = st.selectbox(t("城市/地区列 (可选)", "City/Region Column (Optional)"), cols, index=None)
            c_cat = st.selectbox(t("产品类别列 (可选)", "Category Column (Optional)"), cols, index=None)
            c_qty = st.selectbox(t("销量/件数列 (可选)", "Quantity Column (Optional)"), cols, index=None)
            # 🌟 修复了 columns 的 Bug，并添加了成本列
            c_cost = st.selectbox(t("选择总成本列 (可选，用于计算利润)", "Select Total Cost Column (Optional, for Profit)"), [""] + cols, index=0)
            
            if st.form_submit_button(t("生成分析看板", "Generate Dashboard")):
                if not c_sales: 
                    st.error(t("销售列必填！", "Sales column is required!"))
                else:
                    # 🌟 把 c_cost 也存进 config 字典里
                    st.session_state.analysis_config = {
                        'col_sales': c_sales, 'col_date': c_date, 
                        'col_city': c_city, 'col_cat': c_cat, 'col_qty': c_qty, 'col_cost': c_cost
                    }
                    switch_page('merchant_data_result')

# ==========================================
# 5. 页面渲染函数
# ==========================================
# ==========================================
# 5. 页面渲染函数 (全互动高级版)
# ==========================================
def page_merchant_data_result():
    st.title(t("📊 历史销售数据分析看板", "📊 Historical Sales Analysis Dashboard"))
    if st.button(t("返回上一页", "Back")): 
        switch_page('merchant_upload')
        
    config = st.session_state.analysis_config
    df = load_uploaded_data(st.session_state.uploaded_file).copy()
    c_sales = config.get('col_sales')
    c_date = config.get('col_date')
    c_city = config.get('col_city')
    c_cat = config.get('col_cat')
    c_qty = config.get('col_qty')
    c_cost = config.get('col_cost')

    # 清洗销售额数据
    df[c_sales] = pd.to_numeric(df[c_sales].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
    df = df[df[c_sales] > 0]

    import plotly.express as px

    # ---------------------------------------------------------
    # 1. 基础柱状图和饼图 (Plotly 互动版)
    # ---------------------------------------------------------
    if c_city or c_cat:
        num_plots = sum([bool(c_city), bool(c_cat)])
        cols = st.columns(num_plots)
        col_idx = 0
        
        if c_city:
            with cols[col_idx]:
                city_sales = df.groupby(c_city)[c_sales].sum().reset_index().sort_values(by=c_sales, ascending=False).head(10)
                fig_city = px.bar(
                    city_sales, x=c_sales, y=c_city, orientation='h', 
                    title=f'{c_city} {t("销售额 Top 10", "Sales Top 10")}',
                    color=c_sales, color_continuous_scale='viridis'
                )
                fig_city.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=40, b=0))
                fig_city.update_traces(hovertemplate="<b>%{y}</b><br>销售额: ¥%{x:,.2f}<extra></extra>")
                st.plotly_chart(fig_city, use_container_width=True)
            col_idx += 1
            
        if c_cat:
            with cols[col_idx]:
                cat_sales = df.groupby(c_cat)[c_sales].sum().reset_index()
                fig_cat = px.pie(
                    cat_sales, names=c_cat, values=c_sales, 
                    title=f'{c_cat} {t("销售额占比", "Sales Percentage")}',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_cat.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>%{label}</b><br>销售额: ¥%{value:,.2f}<br>占比: %{percent}<extra></extra>")
                fig_cat.update_layout(margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_cat, use_container_width=True)
    else:
        st.info(t("💡 您未选择城市或类别进行细分，以下为全局销售数据：", "💡 No city or category selected. Here is the global sales data:"))
        st.metric(label=t("💰 总销售额 (Total Sales)", "💰 Total Sales"), value=f"¥ {df[c_sales].sum():,.2f}")

    # ---------------------------------------------------------
    # 2. 时间趋势折线图 (Plotly 互动版)
    # ---------------------------------------------------------
    if c_date:
        st.markdown("---")
        st.subheader(t("📈 时间趋势分析", "📈 Time Trend Analysis"))
        
        clean_dates = df[c_date].astype(str).str.replace('年', '-').str.replace('月', '-').str.replace('日', '')
        parsed_dates = pd.to_datetime(clean_dates, errors='coerce')
        
        if parsed_dates.isna().all():
            time_sales = df.groupby(c_date)[c_sales].sum().reset_index()
            time_col_name = c_date
        else:
            df_time = df.copy()
            df_time['Standard_Date'] = parsed_dates
            df_time = df_time.dropna(subset=['Standard_Date'])
            df_time['Month'] = df_time['Standard_Date'].dt.strftime('%Y-%m')
            time_sales = df_time.groupby('Month')[c_sales].sum().reset_index()
            time_col_name = 'Month'
        
        if not time_sales.empty:
            fig_t = px.line(
                time_sales, x=time_col_name, y=c_sales, markers=True, 
                title=t("销售额时间趋势 (按月汇总)", "Sales Time Trend (Monthly)")
            )
            # 设置线条颜色、加粗，并在节点上显示具体数字
            fig_t.update_traces(
                line=dict(color='#ff7f0e', width=3), 
                marker=dict(size=8),
                text=time_sales[c_sales].apply(lambda x: f"{x:,.0f}"),
                textposition="top center",
                mode="lines+markers+text",
                hovertemplate="<b>%{x}</b><br>总销售额: ¥%{y:,.2f}<extra></extra>"
            )
            fig_t.update_layout(
                xaxis_title=t("时间", "Time"), 
                yaxis_title=t("总销售额", "Total Sales"),
                yaxis=dict(range=[0, time_sales[c_sales].max() * 1.2])
            )
            st.plotly_chart(fig_t, use_container_width=True)
        else:
            st.warning(t("日期数据无效，无法生成趋势图。", "Invalid date data, cannot generate trend chart."))

       # ---------------------------------------------------------
    # 3. KMeans 聚类分析图 (Plotly 互动版 - 双图并排)
    # ---------------------------------------------------------
    if c_qty and c_sales:
        st.markdown("---")
        st.subheader(t("🤖 AI 智能商品盈利矩阵 (K-Means)", "🤖 AI Product Profitability Matrix (K-Means)"))
        
        df[c_qty] = pd.to_numeric(df[c_qty].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        df[c_sales] = pd.to_numeric(df[c_sales].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
        
        if c_cost:
            df[c_cost] = pd.to_numeric(df[c_cost].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
            agg_dict = {c_qty: 'sum', c_sales: 'sum', c_cost: 'sum'}
        else:
            agg_dict = {c_qty: 'sum', c_sales: 'sum'}
            
        item_col = c_cat if c_cat else df.columns[0]
        df_cluster = df.groupby(item_col).agg(agg_dict).reset_index()
        df_cluster = df_cluster[df_cluster[c_qty] > 0]
        
        if len(df_cluster) >= 3:
            # 无论如何，先计算出“平均件单价”
            df_cluster['Unit_Price'] = df_cluster[c_sales] / df_cluster[c_qty]
            
            # 判断是否有成本列，决定右图画“总利润”还是“总销售额”
            if c_cost:
                df_cluster['Total_Profit'] = df_cluster[c_sales] - df_cluster[c_cost]
                metric2_y = 'Total_Profit'
                metric2_label = t("总利润 (Total Profit)", "Total Profit")
                metric2_name = t("总利润", "Total Profit")
                # 使用核心指标(利润)进行聚类
                df_cluster['Cluster'] = run_kmeans_clustering(df_cluster, c_qty, 'Total_Profit').astype(str)
            else:
                df_cluster['Total_Sales'] = df_cluster[c_sales]
                metric2_y = 'Total_Sales'
                metric2_label = t("总销售额 (Total Sales)", "Total Sales")
                metric2_name = t("总销售额", "Total Sales")
                # 使用核心指标(销售额)进行聚类
                df_cluster['Cluster'] = run_kmeans_clustering(df_cluster, c_qty, 'Total_Sales').astype(str)
            
            # 创建左右两列，并排显示两个矩阵图
            col_k1, col_k2 = st.columns(2)
            
            # --- 左图：销量 vs 平均件单价 ---
            with col_k1:
                fig_k1 = px.scatter(
                    df_cluster, x=c_qty, y='Unit_Price', color='Cluster', 
                    text=item_col,
                    title=t("商品定位矩阵：销量 vs 平均件单价", "Product Matrix: Qty vs Unit Price"),
                    color_discrete_sequence=px.colors.qualitative.Set1
                )
                fig_k1.update_traces(
                    textposition='top center', 
                    marker=dict(size=12, opacity=0.8),
                    hovertemplate="<b>%{text}</b><br>总销量: %{x}<br>平均件单价: ¥%{y:,.2f}<extra></extra>"
                )
                fig_k1.update_layout(xaxis_title=t("总销量 (市场热度)", "Total Quantity"), yaxis_title=t("平均件单价 (Unit Price)", "Unit Price"))
                st.plotly_chart(fig_k1, use_container_width=True)
                
            # --- 右图：销量 vs 总利润 (或总销售额) ---
            with col_k2:
                fig_k2 = px.scatter(
                    df_cluster, x=c_qty, y=metric2_y, color='Cluster', 
                    text=item_col,
                    title=f"{t('商品定位矩阵：销量 vs ', 'Product Matrix: Qty vs ')}{metric2_name}",
                    color_discrete_sequence=px.colors.qualitative.Set1
                )
                fig_k2.update_traces(
                    textposition='top center', 
                    marker=dict(size=12, opacity=0.8),
                    hovertemplate="<b>%{text}</b><br>总销量: %{x}<br>" + metric2_name + ": ¥%{y:,.2f}<extra></extra>"
                )
                # 如果有成本，画出红色的盈亏平衡线
                if c_cost:
                    fig_k2.add_hline(y=0, line_dash="dash", line_color="red", annotation_text=t("盈亏平衡线", "Break-even Line"), annotation_position="bottom right")
                fig_k2.update_layout(xaxis_title=t("总销量 (市场热度)", "Total Quantity"), yaxis_title=metric2_label)
                st.plotly_chart(fig_k2, use_container_width=True)
                
            # 输出 AI 诊断清单
            st.info(t(f"💡 AI 诊断说明：系统已根据【市场热度(销量)】与【{metric2_name}】为您划分出明星款与滞销款。", 
                      f"💡 AI Diagnosis: Clustering by Demand (Qty) and {metric2_name}."))
            
            # --- 底部数据表格 (包含所有计算出的指标) ---
            if c_cost:
                cols_to_show = [item_col, c_qty, 'Unit_Price', 'Total_Profit', c_sales, 'Cluster']
                rename_dict = {item_col: t("商品名称", "Product Name"), c_qty: t("总销量", "Total Qty"), 'Unit_Price': t("平均件单价", "Avg Unit Price"), 'Total_Profit': t("总利润", "Total Profit"), c_sales: t("总销售额", "Total Sales"), 'Cluster': t("AI 判定类别", "AI Cluster")}
            else:
                cols_to_show = [item_col, c_qty, 'Unit_Price', 'Total_Sales', 'Cluster']
                rename_dict = {item_col: t("商品名称", "Product Name"), c_qty: t("总销量", "Total Qty"), 'Unit_Price': t("平均件单价", "Avg Unit Price"), 'Total_Sales': t("总销售额", "Total Sales"), 'Cluster': t("AI 判定类别", "AI Cluster")}
                
            df_display = df_cluster[cols_to_show].rename(columns=rename_dict)
            
            # 格式化保留两位小数
            df_display[t("平均件单价", "Avg Unit Price")] = df_display[t("平均件单价", "Avg Unit Price")].round(2)
            if c_cost:
                df_display[t("总利润", "Total Profit")] = df_display[t("总利润", "Total Profit")].round(2)
            df_display[t("总销售额", "Total Sales")] = df_display[t("总销售额", "Total Sales")].round(2)
            
            st.dataframe(df_display.sort_values(by=[t("AI 判定类别", "AI Cluster"), t("总销量", "Total Qty")], ascending=[True, False]), use_container_width=True)


def page_merchant_survey_filter():
    st.title(t("查看公众需求调研结果", "View Public Survey Results"))
    
    # 补全 5 个时间维度
    time_options = [
        t("一个星期", "1 Week"), 
        t("一个月", "1 Month"), 
        t("三个月", "3 Months"), 
        t("六个月", "6 Months"), 
        t("一年", "1 Year")
    ]
    time_range = st.selectbox(t("时间范围", "Time Range"), time_options, index=None)
    filter_prov = st.selectbox(t("筛选省份", "Filter by Province"), ["全部 (All)"] + list(REGION_DICT.keys()), index=0)
    
    if st.button(t("查看结果", "View Results")):
        if not time_range: 
            st.error(t("请选择时间！", "Please select time!"))
        else:
            st.session_state.survey_time_range = time_range
            st.session_state.survey_filter_prov = filter_prov.replace("全部 (All)", "全部")
            switch_page('merchant_survey_result')
            
    if st.button(t("返回", "Back")): 
        switch_page('merchant_dashboard')

def page_merchant_survey_result():
    st.title(t("📈 市场公众需求洞察报告", "📈 Market Public Demand Report"))
    if st.button(t("返回上一页", "Back")): 
        switch_page('merchant_survey_filter')
        
    df = load_survey_data(DB_FILE).copy()
    if df.empty:
        st.warning(t("暂无数据！", "No data available!"))
        return
    
    # 1. 基础大类筛选
    df = df[df['大类'] == st.session_state.merchant_category]
    
    # 2. 真正生效的时间筛选逻辑 (长包含短)
    time_range = st.session_state.get('survey_time_range', '')
    if time_range and '提交时间' in df.columns:
        df['提交时间'] = pd.to_datetime(df['提交时间'], errors='coerce')
        now = pd.Timestamp.now()
        
        # 根据选项计算回溯的截止日期
        if "Week" in time_range or "星期" in time_range:
            cutoff = now - pd.Timedelta(days=7)
        elif "1 Month" in time_range or "一个月" in time_range:
            cutoff = now - pd.Timedelta(days=30)
        elif "3 Months" in time_range or "三个月" in time_range:
            cutoff = now - pd.Timedelta(days=90)
        elif "6 Months" in time_range or "六个月" in time_range:
            cutoff = now - pd.Timedelta(days=180)
        elif "Year" in time_range or "一年" in time_range:
            cutoff = now - pd.Timedelta(days=365)
        else:
            cutoff = None
            
        # 执行筛选：保留提交时间大于等于截止日期的数据
        if cutoff is not None:
            df = df[df['提交时间'] >= cutoff]

    # 3. 省份筛选
    prov_filter = st.session_state.get('survey_filter_prov', '全部')
    if '省份' in df.columns and prov_filter != '全部': 
        df = df[df['省份'] == prov_filter]

    if len(df) == 0:
        st.info(t("该筛选条件下暂无数据。", "No data for this filter condition."))
        return
        
    # 2x2 核心图表看板
    st.subheader(t("📊 核心调研指标分布", "📊 Core Survey Metrics Distribution"))
    
    import plotly.express as px
    
    # 使用 Streamlit 的列布局来代替 matplotlib 的 subplots
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    
    # --- 图 1：最期待单品 Top 排行 ---
    with row1_col1:
        demand_counts = df['期待单品'].value_counts().reset_index()
        demand_counts.columns = ['单品', '数量']
        # 计算占比用于悬停显示
        total_demand = demand_counts['数量'].sum()
        demand_counts['占比'] = (demand_counts['数量'] / total_demand * 100).round(1).astype(str) + '%'
        
        fig1 = px.bar(
            demand_counts, x='数量', y='单品', orientation='h', 
            title=t('最期待单品 Top 排行', 'Top Desired Items'),
            color='数量', color_continuous_scale='magma'
        )
        fig1.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0, r=0, t=40, b=0))
        fig1.update_traces(hovertemplate="<b>%{y}</b><br>选择人数: %{x} 人<br>占比: %{customdata[0]}<extra></extra>", customdata=demand_counts[['占比']])
        st.plotly_chart(fig1, use_container_width=True)
        
    # --- 图 2：期待价格区间分布 ---
    with row1_col2:
        if '期待价格' in df.columns:
            price_counts = df['期待价格'].value_counts().reset_index()
            price_counts.columns = ['价格区间', '数量']
            fig2 = px.pie(
                price_counts, names='价格区间', values='数量',
                title=t('期待价格区间分布', 'Expected Price Distribution'),
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig2.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>%{label}</b><br>选择人数: %{value} 人<br>占比: %{percent}<extra></extra>")
            fig2.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig2, use_container_width=True)
            
    # --- 图 3：线下广告能否提高购买欲 ---
    with row2_col1:
        if '线下广告提高购买欲' in df.columns:
            ad_counts = df['线下广告提高购买欲'].value_counts().reset_index()
            ad_counts.columns = ['态度', '数量']
            fig3 = px.pie(
                ad_counts, names='态度', values='数量',
                title=t('线下广告能否提高购买欲', 'Can Offline Ads Increase Desire?'),
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig3.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>%{label}</b><br>选择人数: %{value} 人<br>占比: %{percent}<extra></extra>")
            fig3.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig3, use_container_width=True)
            
    # --- 图 4：线下服务能否提高购买欲 ---
    with row2_col2:
        if '线下服务提高购买欲' in df.columns:
            svc_counts = df['线下服务提高购买欲'].value_counts().reset_index()
            svc_counts.columns = ['态度', '数量']
            fig4 = px.pie(
                svc_counts, names='态度', values='数量',
                title=t('线下服务能否提高购买欲', 'Can Offline Services Increase Desire?'),
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig4.update_traces(textposition='inside', textinfo='percent+label', hovertemplate="<b>%{label}</b><br>选择人数: %{value} 人<br>占比: %{percent}<extra></extra>")
            fig4.update_layout(margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig4, use_container_width=True)

        # 建议与业务洞察 (高级互动版)
    st.markdown("---")
    st.subheader(t("💬 公众具体建议与业务洞察", "💬 Public Suggestions & Business Insights"))
    
    # 确保导入了 plotly (如果没有安装，记得在终端运行 pip install plotly)
    import plotly.express as px
    
    sug_data = []
    for _, row in df.iterrows():
        # 严格按照问卷大类进行归类
        if pd.notna(row.get('建议_广告')) and str(row['建议_广告']).strip(): 
            sug_data.append({'时间': row['提交时间'], '城市': row['城市'], '建议类型': '📢 线下广告与推广建议', '内容': str(row['建议_广告'])})
        if pd.notna(row.get('建议_感受')) and str(row['建议_感受']).strip(): 
            sug_data.append({'时间': row['提交时间'], '城市': row['城市'], '建议类型': '🛍️ 门店服务与体验期望', '内容': str(row['建议_感受'])})
        if pd.notna(row.get('建议_折扣')) and str(row['建议_折扣']).strip(): 
            sug_data.append({'时间': row['提交时间'], '城市': row['城市'], '建议类型': '🎁 促销与活动期望', '内容': str(row['建议_折扣'])})
            
    if sug_data:
        df_sug = pd.DataFrame(sug_data)
        
        # 1. 顶部筛选器
        all_types = [t('全部 (All)', 'All')] + list(df_sug['建议类型'].unique())
        selected_type = st.selectbox(t("🔍 筛选业务维度：", "🔍 Filter by Business Dimension:"), all_types)
        
        if selected_type != t('全部 (All)', 'All'):
            df_sug = df_sug[df_sug['建议类型'] == selected_type]
            
        search_kw = st.text_input("🔍 " + t("搜索关键词 过滤建议", "Search Keywords (Filter Suggestions)"))
        if search_kw: 
            df_sug = df_sug[df_sug['内容'].str.contains(search_kw, case=False, na=False)]
            
        if not df_sug.empty:
            col_chart, col_kw = st.columns([1.2, 1]) # 左边图表稍微宽一点
            
            with col_chart:
                st.markdown(f"**{t('📊 各类建议占比 (鼠标悬停查看 AI 洞察)', '📊 Suggestion Distribution (Hover for AI Insights)')}**")
                
                # 准备 Plotly 互动图表的数据
                category_summary = []
                for cat in df_sug['建议类型'].unique():
                    cat_df = df_sug[df_sug['建议类型'] == cat]
                    total_count = len(cat_df)
                    
                    # 提取该类别的高频词
                    top_words = extract_keywords(cat_df['内容'].tolist(), top_n=5)
                    hover_text = ""
                    if top_words:
                        word_lines = []
                        for word, freq in top_words:
                            # 计算出现比例：该词出现的次数 / 该类别的总建议数
                            pct = (freq / total_count) * 100
                            word_lines.append(f"▪ <b>{word}</b>: {pct:.1f}%")
                        hover_text = "<br>".join(word_lines)
                    else:
                        hover_text = "暂无高频词"
                        
                    category_summary.append({
                        '建议类型': cat,
                        '数量': total_count,
                        'HoverText': hover_text
                    })
                
                df_summary = pd.DataFrame(category_summary)
                
                # 绘制高级互动环形图
                fig_pie = px.pie(
                    df_summary, 
                    names='建议类型', 
                    values='数量', 
                    hole=0.45, # 环形图空心大小
                    custom_data=['HoverText'], # 将高频词数据传入图表
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                
                # 自定义鼠标悬停时弹出的信息卡片 (Tooltip)
                fig_pie.update_traces(
                    hovertemplate="<b>%{label}</b><br>" +
                                  "总建议数: %{value} 条<br>" +
                                  "<br><b>🔥 AI 提取核心诉求 (提及率):</b><br>%{customdata[0]}" +
                                  "<extra></extra>" # 隐藏多余的尾巴
                )
                fig_pie.update_layout(margin=dict(t=20, b=20, l=0, r=0))
                
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col_kw:
                # 右侧保留全局的高频词柱状图，方便截图和静态展示
                st.markdown(f"**{t('🧠 当前视图核心诉求', '🧠 Current View Core Demands')}**")
                top_words = extract_keywords(df_sug['内容'].tolist(), top_n=8)
                if top_words:
                    words, counts = zip(*top_words)
                    fig_kw, ax_kw = plt.subplots(figsize=(5, 4.5))
                    sns.barplot(x=list(counts), y=list(words), ax=ax_kw, palette='Blues_r')
                    ax_kw.set_title(t("高频词 Top 8", "Top 8 Keywords"))
                    ax_kw.set_xlabel(t("提及次数", "Mentions"))
                    st.pyplot(fig_kw)
                else:
                    st.info(t("文本太少，无法提取高频词。", "Not enough text for keywords."))
            
            # 建议明细表格
            st.markdown("##### " + t("📋 建议明细工单", "📋 Suggestion Details Ticket"))
            st.markdown("""
                <style>
                    [data-testid="stDataFrame"] { font-size: 16px !important; }
                </style>
            """, unsafe_allow_html=True)
            st.dataframe(df_sug[['建议类型', '内容', '城市', '时间']], use_container_width=True, hide_index=True)
        else: 
            st.info(t("没有符合条件的建议。", "No suggestions match the criteria."))
    else: 
        st.info(t("暂无具体建议数据。", "No specific suggestions available."))
    
    # 供需对比
    st.markdown("---")
    st.subheader(t("⚖️ 现有销售数据 vs 公众需求对比", "⚖️ Actual Sales vs Public Demand Comparison"))
    comp_file = st.file_uploader(t("上传现有销售数据 (CSV/Excel)", "Upload Sales Data"), type=['csv', 'xlsx'])
    
    if comp_file:
        df_actual = load_uploaded_data(comp_file)
        col_item = st.selectbox(t("选择商品名称列 (如色号/款式) 【必填】", "Select Item Name Column [Required]"), df_actual.columns, index=None)
        col_sales = st.selectbox(t("选择销量/销售额列 【必填】", "Select Sales/Qty Column [Required]"), df_actual.columns, index=None)
        
        filter_cols = st.multiselect(t("选择需要筛选的列 (可选)", "Select columns to filter (Optional)"), df_actual.columns)
        active_filters = {}
        if filter_cols:
            cols = st.columns(min(len(filter_cols), 3))
            for i, col in enumerate(filter_cols):
                with cols[i % 3]:
                    unique_vals = ["全部 (All)"] + list(df_actual[col].dropna().astype(str).unique())
                    selected_val = st.selectbox(f"{t('筛选', 'Filter')} [{col}]", unique_vals, index=0)
                    if selected_val != "全部 (All)": 
                        active_filters[col] = selected_val
            
        if st.button(t("生成对比图", "Generate Comparison Plot")):
            if col_item and col_sales:
                for col, val in active_filters.items(): 
                    df_actual = df_actual[df_actual[col].astype(str) == val]
                    
                if df_actual.empty: 
                    st.warning(t("当前筛选条件下无实际销售数据！", "No actual sales data for current filters!"))
                else:
                    df_actual[col_sales] = pd.to_numeric(df_actual[col_sales].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce').fillna(0)
                    actual_agg = df_actual.groupby(col_item)[col_sales].sum()
                    actual_pct = (actual_agg / actual_agg.sum() * 100).rename(t("实际销售占比 (%)", "Actual Sales (%)"))
                    demand_pct_renamed = demand_pct.rename(t("公众期望占比 (%)", "Public Demand (%)"))
                    comp_df = pd.concat([actual_pct, demand_pct_renamed], axis=1).fillna(0)
                    
                    fig2, ax2 = plt.subplots(figsize=(10, 6))
                    comp_df.plot(kind='bar', ax=ax2, color=['#1f77b4', '#ff7f0e'])
                    ax2.set_ylabel(t("百分比 (%)", "Percentage (%)"))
                    ax2.set_title(t("实际销售 和 公众期望 差异对比", "Actual Sales and Public Demand"))
                    plt.xticks(rotation=45)
                    st.pyplot(fig2)
            else: 
                st.error(t("请选择用于对比的商品名称和销售列！", "Please select item name and sales columns!"))

# ==========================================
# 6. 主程序入口
# ==========================================
def main():
    pages = {
        'lang_select': page_lang_select, 
        'home': page_home, 
        'merchant_login': page_merchant_login, 
        'public_info': page_public_info, 
        'merchant_dashboard': page_merchant_dashboard, 
        'public_survey': page_public_survey, 
        'merchant_upload': page_merchant_upload, 
        'merchant_survey_filter': page_merchant_survey_filter, 
        'public_thanks': page_public_thanks, 
        'merchant_data_result': page_merchant_data_result, 
        'merchant_survey_result': page_merchant_survey_result,
        'tech_portal': page_tech_portal
    }
    pages[st.session_state.page]()
    st.markdown("<div style='position: fixed; bottom: 10px; right: 20px; color: gray; font-size: 14px;'>Producer: 23D011 SONG JIARUI</div>", unsafe_allow_html=True)

if __name__ == "__main__": 
    main()
