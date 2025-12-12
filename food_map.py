import pandas as pd
import folium
import os
import webbrowser
import re  # 處理價位字串
from folium.plugins import MarkerCluster  # YouBike 站點用群聚標記

def price_to_radius(price_str):
    """
    把價位字串(例如 '50-120', '200~400') 轉成一個半徑數字。
    價位越高，圓圈越大。只是大概分級，不用太精準。
    """
    avg_price = 100

    if isinstance(price_str, str):
        parts = re.split(r"[-~～至到]", price_str)
        nums = []
        for p in parts:
            p = p.strip()
            if p.isdigit():
                nums.append(int(p))
        if len(nums) >= 1:
            low = nums[0]
            high = nums[-1] if len(nums) > 1 else low
            avg_price = (low + high) / 2
    else:
        try:
            avg_price = float(price_str)
        except Exception:
            pass

    radius = avg_price / 20
    radius = max(4, min(radius, 20))  # 限制在 4~20
    return radius


def main():
    # 1. 讀入美食資料
    csv_path = "foods.csv"
    df = pd.read_csv(csv_path, encoding="utf-8")

    # 2. 設定地圖中心點
    center_lat = df["lat"].mean()
    center_lon = df["lon"].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=15)

    # 3. 各類別圖層
    category_groups = {}
    for cat in df["category"].dropna().unique():
        group = folium.FeatureGroup(name=f"類別：{cat}")
        group.add_to(m)
        category_groups[cat] = group

    # 4. 顏色設定
    category_color = {
        "早餐": "blue",
        "午餐": "green",
        "晚餐": "red",
        "宵夜": "purple",
        "下午茶": "orange",
        "飲料": "cadetblue"
    }

    # 5. 氣泡圖圖層
    bubble_group = folium.FeatureGroup(name="氣泡圖（價位越高圈越大）")
    bubble_group.add_to(m)

    # 6. 把每一間店加入：一般標記 + 氣泡圈
    for _, row in df.iterrows():
        name = row["name"]
        lat = row["lat"]
        lon = row["lon"]
        category = row.get("category", "")
        price = row.get("price", "")
        intro = row.get("intro", "")

        # ---- 一般 marker ----
        group = category_groups.get(category)
        if group is None:
            if "其他" not in category_groups:
                other_group = folium.FeatureGroup(name="類別：其他")
                other_group.add_to(m)
                category_groups["其他"] = other_group
            group = category_groups["其他"]

        color = category_color.get(category, "gray")

        popup_html = f"""
<div style="width:250px; font-size:14px;">
    <b style="font-size:16px;">{name}</b><br>
    <b>類別：</b>{category}<br>
    <b>價位：</b>{price}<br>
    <b>簡介：</b>{intro}
</div>
"""


        folium.Marker(
            location=[lat, lon],
            tooltip=name,
            popup=popup_html,
            icon=folium.Icon(color=color)
        ).add_to(group)

        # ---- 氣泡圖 ----
        radius = price_to_radius(price)
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            popup=popup_html,
            tooltip=name,
            color="orange",
            fill=True,
            fill_color="orange",
            fill_opacity=0.5
        ).add_to(bubble_group)

    # 7. 加入 YouBike 站點圖層
    ubike_df = pd.read_csv("Youbike2.0.csv", encoding="utf-8-sig")

    ubike_group = folium.FeatureGroup(name="YouBike 站點")
    ubike_group.add_to(m)

    cluster = MarkerCluster().add_to(ubike_group)

    for _, r in ubike_df.iterrows():
        lat = r["lat"]
        lng = r["lng"]
        station = str(r["station"])

        folium.Marker(
            location=[lat, lng],
            tooltip=f"YouBike：{station}",
            popup=f"YouBike 站點：{station}",
            icon=folium.CustomIcon(
                'youbike_icon.png',   # 圖檔檔名
                icon_size=(30, 30)    # 圖示大小
            )
        ).add_to(cluster)



    # 8. 圖層控制
    folium.LayerControl(collapsed=False).add_to(m)

    # 9. 輸出 HTML
    output_file = "food_map.html"
    m.save(output_file)
    print(f"地圖已產生：{output_file}")

    full_path = os.path.abspath(output_file)
    webbrowser.open("file://" + full_path)

if __name__ == "__main__":
    main()
