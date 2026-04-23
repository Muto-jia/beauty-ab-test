# 导入库
import numpy as np
import pandas as pd
from scipy import stats
from matplotlib import pyplot as plt
from sqlalchemy import create_engine

# ==========================================
# 【这里只需要你改 4 个地方！】
# ==========================================
username = "root"           # 你的MySQL用户名（一般都是root）
password = "root"       # 你的MySQL密码
host = "localhost"          # 一般不变
database = "beauty_data"    # 你创建的数据库名
# ==========================================

# 构建连接
engine = create_engine(f'mysql+pymysql://{username}:{password}@{host}:3306/{database}')

# 测试连接：从MySQL读数据
try:
    df = pd.read_sql("SELECT * FROM beauty_user_behavior LIMIT 5", engine)
    print("✅ MySQL 连接成功！")
    print("读到的数据：")
    print(df)
except Exception as e:
    print("❌ 连接失败：", e)

# 读取数据
df = pd.read_sql("SELECT * FROM beauty_user_behavior", engine)
print("✅ 数据读取成功，总行数：", len(df))

# 4. 数据清洗（去重）
# ----------------------
df = df.drop_duplicates(subset=["user_id", "item_id", "behavior_type", "date", "hour"])
print("✅ 去重完成，有效数据：", len(df))


# 5. 用户哈希分流（核心！）
# A组：浏览排序  |  B组：加购购买排序
# ----------------------
def ab_split(user_id):
    return "A" if hash(str(user_id)) % 100 < 50 else "B"

df["group"] = df["user_id"].apply(ab_split)

# 查看分组人数
user_count = df.groupby("group")["user_id"].nunique()
print("\n===== A/B组用户数 =====")
print(user_count)

# 6. 计算AB组核心指标
# ----------------------
def calc_metrics(data):
    # 浏览
    view = data[data["behavior_type"] == 1].drop_duplicates(subset=["user_id", "item_id"]).shape[0]
    # 加购
    cart = data[data["behavior_type"] == 3].drop_duplicates(subset=["user_id", "item_id"]).shape[0]
    # 购买
    buy  = data[data["behavior_type"] == 4].drop_duplicates(subset=["user_id", "item_id"]).shape[0]
    # 收藏
    coll = data[data["behavior_type"] == 2].drop_duplicates(subset=["user_id", "item_id"]).shape[0]

    # 用户数 & 商品数
    user_num = data["user_id"].nunique()
    item_num = data[data["behavior_type"] == 1]["item_id"].nunique()

    # 指标
    buy_conv = buy / view if view != 0 else 0
    cart_rate = cart / view if view != 0 else 0
    coll_rate = coll / view if view != 0 else 0
    per_buy = buy / user_num if user_num != 0 else 0
    per_item = item_num / user_num if user_num != 0 else 0

    return {
        "用户数": user_num,
        "浏览数": view,
        "加购数": cart,
        "购买数": buy,
        "购买转化率": round(buy_conv, 4),
        "加购率": round(cart_rate, 4),
        "收藏率": round(coll_rate, 4),
        "人均购买次数(人均GMV)": round(per_buy, 4),
        "人均浏览商品数": round(per_item, 4)
    }

# 拆分A组B组
a = df[df["group"] == "A"]
b = df[df["group"] == "B"]

# 计算指标
a_metric = calc_metrics(a)
b_metric = calc_metrics(b)

# 展示结果
print("\n===== A组（浏览排序）指标 =====")
for k, v in a_metric.items():
    print(f"{k}: {v}")

print("\n===== B组（加购/购买排序）指标 =====")
for k, v in b_metric.items():
    print(f"{k}: {v}")

# ----------------------
# 7. 统计检验（看是否显著）
# ----------------------
def chi_test(a_df, b_df, behavior):
    a_success = a_df[a_df["behavior_type"] == behavior].drop_duplicates(subset=["user_id", "item_id"]).shape[0]
    b_success = b_df[b_df["behavior_type"] == behavior].drop_duplicates(subset=["user_id", "item_id"]).shape[0]

    a_view = a_df[a_df["behavior_type"] == 1].shape[0]
    b_view = b_df[b_df["behavior_type"] == 1].shape[0]

    table = [
        [a_success, a_view - a_success],
        [b_success, b_view - b_success]
    ]
    _, p, _, _ = stats.chi2_contingency(table)
    return round(p, 4)

# 检验
p_buy = chi_test(a, b, 4)
p_cart = chi_test(a, b, 3)

print("\n===== 统计显著性 =====")
print(f"购买转化率 p值: {p_buy} → {'显著' if p_buy < 0.05 else '不显著'}")
print(f"加购率 p值: {p_cart} → {'显著' if p_cart < 0.05 else '不显著'}")

# ----------------------
# 8. 画图展示结果
# ----------------------
labels = ["购买转化率", "加购率", "人均GMV", "人均浏览商品数"]
a_vals = [a_metric["购买转化率"], a_metric["加购率"], a_metric["人均购买次数(人均GMV)"], a_metric["人均浏览商品数"]]
b_vals = [b_metric["购买转化率"], b_metric["加购率"], b_metric["人均购买次数(人均GMV)"], b_metric["人均浏览商品数"]]

x = np.arange(len(labels))
width = 0.35

plt.figure(figsize=(12, 5))
plt.bar(x - width/2, a_vals, width, label="A组 浏览排序")
plt.bar(x + width/2, b_vals, width, label="B组 加购/购买排序")

plt.title("A/B测试指标对比")
plt.xticks(x, labels)
plt.legend()
plt.tight_layout()
plt.show()

print("\n🎉 AB测试全部运行完成！")
