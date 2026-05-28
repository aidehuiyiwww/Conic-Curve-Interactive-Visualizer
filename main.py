# ==================================================
# 圆锥曲线交互可视化程序 | Conic Curve Interactive Visualizer
# 主要功能 | Main Functions:
# 1. 实时展示三大圆锥曲线(圆/椭圆/抛物线/双曲线)随离心率连续变化过程
#    Real-time display of conic curves (Circle/Ellipse/Parabola/Hyperbola)
# 2. e/a/b/c 四参数双向联动调节，支持滑块 + 数字输入框两种方式
#    Bidirectional linkage for e/a/b/c, support slider & number input
# 3. 离心率e采用对数拖动，输入框显示真实数值，调节更平滑
#    Logarithmic drag for e, real value displayed in input box
# 4. 可选显示焦点、准线、焦点坐标、准线方程及数学标注标签
#    Optional display of foci, directrices, coordinates and equations
# 5. 坐标轴刻度标注在原点附近，符合数学绘图习惯
#    Axis ticks labeled near origin, conform to mathematical convention
# 6. 一键导出 300DPI 高清图片，适配学术使用
#    One-click export of 300dpi high-resolution academic images
# 7. 固定画布视口，坐标轴范围永久不变，界面稳定不跳动
#    Fixed canvas viewport, axis range locked permanently
# 8. 拖拽滑块实时动态刷新图像，鼠标拖动过程中同步变化
#    Real-time rendering while dragging slider (no need to release mouse)
# 9. 一键停止服务器，无需手动按Ctrl+C
#    One-click stop server, no need for Ctrl+C
#
# 运行方法 | How to Run:
# 1. 安装依赖 | Install dependencies:
#    pip install streamlit numpy matplotlib
# 2. 必须在终端(Terminal/CMD/PowerShell)中执行以下命令，
#    禁止直接在PyCharm/IDE点击运行按钮（会触发运行报错）
#    Run command in Terminal ONLY (DO NOT click IDE run button):
#    streamlit run main.py
# 3. 脱离Python运行方案 | Run without Python environment:
#    方案1: 部署至 Streamlit Community Cloud，通过浏览器链接访问
#    Solution 1: Deploy to Streamlit Community Cloud, access via web link
#    方案2: 使用 pyinstaller 打包为 Windows EXE 可执行文件
#    Solution 2: Package into EXE with pyinstaller
# ==================================================

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import os

# 全局配置
plt.rcParams['axes.unicode_minus'] = False
st.set_page_config(page_title="Conic Curve", layout="wide")

# ====================== 全局样式优化 ======================
st.markdown("""
<style>
/* 彻底隐藏所有Streamlit默认UI */
header { visibility: hidden; height: 0px; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
.stDeployButton { display: none; }

/* 移除所有页面边距，最大化图表显示 */
.block-container {
    padding-top: 0rem !important;
    padding-bottom: 0rem !important;
    padding-left: 0.5rem !important;
    padding-right: 0.5rem !important;
    max-width: 100% !important;
}

/* 参数名称样式：增大字体，减小与滑块的距离 */
.param-title {
    font-size: 16px !important;
    font-weight: bold;
    margin-bottom: 0px !important;
    margin-top: 8px !important;
}

/* 滑块样式：减少与下一个元素的间距 */
div[data-testid="stSlider"] {
    margin-bottom: 0px !important;
    padding-bottom: 0px !important;
}

/* 输入框样式 */
div[data-testid="stNumberInput"] {
    margin-bottom: 0px !important;
}

/* 缩小其他控件字体 */
div[data-testid="stMarkdown"] p {font-size: 12px;}
div[data-testid="stCheckbox"] label {font-size: 12px;}

/* 参数面板样式 */
.param-panel {
    background: rgba(0, 0, 0, 0.85);
    color: white !important;
    padding: 10px;
    border-radius: 6px;
    margin-top: 15px;
    font-size: 12px !important;
}

.param-panel * {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)


# ====================== 高精度数学计算函数 ======================
def update_from_ea(e, a):
    c = e * a
    if e < 1 - 1e-12:
        b = np.sqrt(max(a ** 2 - c ** 2, 1e-12))
        typ = "Ellipse"
    elif abs(e - 1) < 1e-10:
        b = 0.0
        typ = "Parabola"
    else:
        b = np.sqrt(max(c ** 2 - a ** 2, 1e-12))
        typ = "Hyperbola"
    return c, b, typ


def update_from_ac(a, c):
    a = max(a, 1e-12)
    e = c / a
    if e < 1 - 1e-12:
        b = np.sqrt(max(a ** 2 - c ** 2, 1e-12))
        typ = "Ellipse"
    elif abs(e - 1) < 1e-10:
        b = 0.0
        typ = "Parabola"
    else:
        b = np.sqrt(max(c ** 2 - a ** 2, 1e-12))
        typ = "Hyperbola"
    return e, b, typ


def update_from_ab(a, b):
    b = min(b, a - 1e-9)
    c = np.sqrt(max(a ** 2 - b ** 2, 1e-12))
    e = c / a
    return c, e, "Ellipse"


# ====================== 会话状态初始化 ======================
if "e" not in st.session_state:
    st.session_state.e = 0.5
if "a" not in st.session_state:
    st.session_state.a = 5.0
if "c" not in st.session_state:
    st.session_state.c = 2.5
if "b" not in st.session_state:
    st.session_state.b = 4.3301
if "curve_type" not in st.session_state:
    st.session_state.curve_type = "Ellipse"

# ====================== 左侧：滑块+输入框双向联动 + 选项 + 参数面板 ======================
col_left, col_right = st.columns([0.25, 0.75])

with col_left:
    st.markdown("<h4 style='margin-bottom: 15px; text-align: center;'>Parameters</h4>", unsafe_allow_html=True)

    # ------------------ 离心率e：对数拖动+输入框显示真实值 ------------------
    st.markdown("<div class='param-title'>Eccentricity e</div>", unsafe_allow_html=True)
    col_e_slider, col_e_input = st.columns([3, 1])
    with col_e_slider:
        # 滑块显示log10(e)，范围-4~2对应e=0.0001~100
        log_e = np.log10(st.session_state.e)
        slider_log_e = st.slider(
            "",
            min_value=-4.0,
            max_value=2.0,
            value=log_e,
            step=0.005,
            format="log(e)=%.2f"
        )
        new_e_slider = 10 ** slider_log_e
    with col_e_input:
        input_e = st.number_input(
            "",
            min_value=0.0001,
            max_value=100.0,
            value=st.session_state.e,
            step=0.001,
            format="%.4f"
        )

    # 优先使用输入框的值
    if abs(input_e - st.session_state.e) > 1e-9:
        new_e = input_e
    else:
        new_e = new_e_slider

    # ------------------ 半长轴a：滑块+输入框双向联动 ------------------
    st.markdown("<div class='param-title'>Semi-major axis a</div>", unsafe_allow_html=True)
    col_a_slider, col_a_input = st.columns([3, 1])
    with col_a_slider:
        new_a_slider = st.slider(
            "",
            min_value=0.1,
            max_value=10.0,
            value=st.session_state.a,
            step=0.05,
            format="%.1f"
        )
    with col_a_input:
        input_a = st.number_input(
            "",
            min_value=0.1,
            max_value=10.0,
            value=st.session_state.a,
            step=0.01,
            format="%.2f"
        )

    if abs(input_a - st.session_state.a) > 1e-9:
        new_a = input_a
    else:
        new_a = new_a_slider

    # ------------------ 半焦距c：滑块+输入框双向联动 ------------------
    st.markdown("<div class='param-title'>Semi-focal length c</div>", unsafe_allow_html=True)
    col_c_slider, col_c_input = st.columns([3, 1])
    with col_c_slider:
        # 动态调整c的最大值，避免超限
        max_c = min(1000.0, new_e * 10.0)
        new_c_slider = st.slider(
            "",
            min_value=0.0001,
            max_value=max_c,
            value=min(st.session_state.c, max_c),
            step=0.01,
            format="%.2f"
        )
    with col_c_input:
        input_c = st.number_input(
            "",
            min_value=0.0001,
            max_value=1000.0,
            value=st.session_state.c,
            step=0.01,
            format="%.2f"
        )

    if abs(input_c - st.session_state.c) > 1e-9:
        new_c = input_c
    else:
        new_c = new_c_slider

    # ------------------ 半短轴b：滑块+输入框双向联动 ------------------
    st.markdown("<div class='param-title'>Semi-minor axis b</div>", unsafe_allow_html=True)
    col_b_slider, col_b_input = st.columns([3, 1])
    with col_b_slider:
        # 动态调整b的最大值，避免超限
        if new_e < 1:
            max_b = new_a - 1e-3
        else:
            max_b = 100.0
        new_b_slider = st.slider(
            "",
            min_value=0.0,
            max_value=max_b,
            value=min(st.session_state.b, max_b),
            step=0.01,
            format="%.2f"
        )
    with col_b_input:
        input_b = st.number_input(
            "",
            min_value=0.0,
            max_value=1000.0,
            value=st.session_state.b,
            step=0.01,
            format="%.2f"
        )

    if abs(input_b - st.session_state.b) > 1e-9:
        new_b = input_b
    else:
        new_b = new_b_slider

    # ------------------ 安全参数联动计算（彻底解决超限问题） ------------------
    try:
        if abs(new_e - st.session_state.e) > 1e-9 or abs(new_a - st.session_state.a) > 1e-9:
            new_c, new_b, new_typ = update_from_ea(new_e, new_a)
        elif abs(new_c - st.session_state.c) > 1e-9:
            new_e, new_b, new_typ = update_from_ac(new_a, new_c)
        elif abs(new_b - st.session_state.b) > 1e-9 and st.session_state.curve_type == "Ellipse":
            new_c, new_e, new_typ = update_from_ab(new_a, new_b)
        else:
            new_typ = st.session_state.curve_type

        # 最终安全检查：确保所有参数都在合理范围内
        new_e = np.clip(new_e, 0.0001, 100.0)
        new_a = np.clip(new_a, 0.1, 10.0)
        new_c = np.clip(new_c, 0.0001, 1000.0)
        new_b = np.clip(new_b, 0.0, 1000.0)

    except:
        # 发生任何错误时，使用上一次的有效值
        new_e = st.session_state.e
        new_a = st.session_state.a
        new_c = st.session_state.c
        new_b = st.session_state.b
        new_typ = st.session_state.curve_type

    # 显示选项（新增焦点坐标和准线方程）
    st.markdown("<hr style='margin: 15px 0 8px 0;'>", unsafe_allow_html=True)
    show_foci = st.checkbox("Show Foci", value=True)
    show_foci_coords = st.checkbox("Show Foci Coordinates", value=False)
    show_directrix = st.checkbox("Show Directrix", value=False)
    show_directrix_eq = st.checkbox("Show Directrix Equations", value=False)
    show_labels = st.checkbox("Show Labels", value=True)

    # ------------------ 左下角参数面板 ------------------
    if st.session_state.curve_type == "Ellipse":
        equation = r"$\frac{x^2}{a^2}+\frac{y^2}{b^2}=1$"
    elif st.session_state.curve_type == "Parabola":
        equation = r"$y^2=4ax$"
    else:
        equation = r"$\frac{x^2}{a^2}-\frac{y^2}{b^2}=1$"

    st.markdown(f"""
    <div class="param-panel">
    <b>Conic Curve</b><br>
    Equation: {equation}<br>
    Type: {st.session_state.curve_type}<br>
    e = {st.session_state.e:.4f}<br>
    a = {st.session_state.a:.2f}<br>
    b = {st.session_state.b:.2f}<br>
    c = {st.session_state.c:.2f}
    </div>
    """, unsafe_allow_html=True)

    # 一键停止服务器
    st.markdown("<hr style='margin: 15px 0 8px 0;'>", unsafe_allow_html=True)
    if st.button("Stop Server", use_container_width=True):
        st.success("Server stopped")
        os._exit(0)

# 更新全局参数
st.session_state.e = float(new_e)
st.session_state.a = float(new_a)
st.session_state.c = float(new_c)
st.session_state.b = float(new_b)
st.session_state.curve_type = new_typ

# ====================== 右侧：永久固定坐标轴图表（彻底解决封顶问题） ======================
with col_right:
    e = st.session_state.e
    a = st.session_state.a
    c = st.session_state.c
    b = st.session_state.b
    typ = st.session_state.curve_type

    FIG_SIZE = (14, 9)
    FIX_X_LIM = (-12, 12)
    FIX_Y_LIM = (-8, 8)

    # 预创建画布并强制锁定坐标轴（三重保险）
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=100)
    ax.set_xlim(FIX_X_LIM)
    ax.set_ylim(FIX_Y_LIM)
    ax.autoscale(enable=False, axis='both')  # 彻底禁用自动缩放
    ax.set_autoscale_on(False)
    ax.set_aspect('equal', adjustable='box')

    # ====================== 坐标轴原点刻度 ======================
    # 移动坐标轴到原点(0,0)
    ax.spines['left'].set_position('zero')
    ax.spines['bottom'].set_position('zero')
    # 隐藏顶部和右侧的轴
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # 调整刻度位置
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    # 设置刻度字体大小
    ax.tick_params(axis='both', labelsize=10)

    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_title("Conic Curve", fontsize=14, pad=10)

    # 优化采样点数：平衡速度与平滑度
    x = np.linspace(FIX_X_LIM[0], FIX_X_LIM[1], 2000)

    # ====================== 正确绘图（移除错误的y值截断） ======================
    if typ == "Ellipse":
        mask = np.abs(x) <= a
        x_ell = x[mask]
        y_upper = b * np.sqrt(1 - (x_ell ** 2) / (a ** 2))
        ax.plot(x_ell, y_upper, linewidth=2.5, color='#1f77b4')
        ax.plot(x_ell, -y_upper, linewidth=2.5, color='#1f77b4')

    elif typ == "Parabola":
        x_par = np.linspace(0, FIX_X_LIM[1], 1500)
        y_upper = np.sqrt(4 * a * x_par)
        ax.plot(x_par, y_upper, linewidth=2.5, color='#1f77b4')
        ax.plot(x_par, -y_upper, linewidth=2.5, color='#1f77b4')

    else:  # 双曲线
        x_right = np.linspace(a, FIX_X_LIM[1], 1000)
        y_right = b * np.sqrt((x_right ** 2) / (a ** 2) - 1)
        ax.plot(x_right, y_right, linewidth=2.5, color='#1f77b4')
        ax.plot(x_right, -y_right, linewidth=2.5, color='#1f77b4')

        x_left = np.linspace(FIX_X_LIM[0], -a, 1000)
        y_left = b * np.sqrt((x_left ** 2) / (a ** 2) - 1)
        ax.plot(x_left, y_left, linewidth=2.5, color='#1f77b4')
        ax.plot(x_left, -y_left, linewidth=2.5, color='#1f77b4')

    # ====================== 绘制焦点和准线 ======================
    if show_foci:
        if typ in ("Ellipse", "Hyperbola"):
            # 只绘制在坐标轴范围内的焦点
            if -c > FIX_X_LIM[0] and -c < FIX_X_LIM[1]:
                ax.scatter(-c, 0, color='#d62728', s=60, zorder=5)
                if show_labels:
                    ax.text(-c - 0.4, 0.3, '$F_1$', fontsize=10, color='#d62728')
                if show_foci_coords:
                    ax.text(-c, -0.6, f'({-c:.2f}, 0)', fontsize=9, color='#d62728', ha='center')
            if c > FIX_X_LIM[0] and c < FIX_X_LIM[1]:
                ax.scatter(c, 0, color='#d62728', s=60, zorder=5)
                if show_labels:
                    ax.text(c + 0.2, 0.3, '$F_2$', fontsize=10, color='#d62728')
                if show_foci_coords:
                    ax.text(c, -0.6, f'({c:.2f}, 0)', fontsize=9, color='#d62728', ha='center')
        elif typ == "Parabola":
            if a > FIX_X_LIM[0] and a < FIX_X_LIM[1]:
                ax.scatter(a, 0, color='#d62728', s=60, zorder=5)
                if show_labels:
                    ax.text(a + 0.2, 0.3, '$F$', fontsize=10, color='#d62728')
                if show_foci_coords:
                    ax.text(a, -0.6, f'({a:.2f}, 0)', fontsize=9, color='#d62728', ha='center')

    if show_directrix:
        if typ in ("Ellipse", "Hyperbola"):
            d = a / e
            # 只绘制在坐标轴范围内的准线
            if d > FIX_X_LIM[0] and d < FIX_X_LIM[1]:
                ax.axvline(x=d, color='#2ca02c', linestyle='--', linewidth=1.5)
                if show_directrix_eq:
                    ax.text(d, FIX_Y_LIM[1] * 0.9, f'x={d:.2f}', fontsize=9, color='#2ca02c', ha='center')
            if -d > FIX_X_LIM[0] and -d < FIX_X_LIM[1]:
                ax.axvline(x=-d, color='#2ca02c', linestyle='--', linewidth=1.5)
                if show_directrix_eq:
                    ax.text(-d, FIX_Y_LIM[1] * 0.9, f'x={-d:.2f}', fontsize=9, color='#2ca02c', ha='center')
        elif typ == "Parabola":
            if -a > FIX_X_LIM[0] and -a < FIX_X_LIM[1]:
                ax.axvline(x=-a, color='#2ca02c', linestyle='--', linewidth=1.5)
                if show_directrix_eq:
                    ax.text(-a, FIX_Y_LIM[1] * 0.9, f'x={-a:.2f}', fontsize=9, color='#2ca02c', ha='center')

    # 最终强制锁定坐标轴（三重保险）
    ax.set_xlim(FIX_X_LIM)
    ax.set_ylim(FIX_Y_LIM)
    ax.autoscale(enable=False, axis='both')

    # 展示图表
    st.pyplot(fig, use_container_width=True)

    # 导出按钮
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    st.download_button(
        label="📥 Export 300dpi PNG",
        data=buf,
        file_name=f"conic_e={e:.4f}.png",
        mime="image/png",
        use_container_width=True
    )

# 运行命令：streamlit run main.py