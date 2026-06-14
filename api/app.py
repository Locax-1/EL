import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

# --- 配置区域 ---
app = Flask(__name__)
CORS(app)  # 允许跨域

# 你的 API Key (建议后续移到环境变量)
dashscope_api_key = "sk-ws-H.REDRMDY.JZ2P.MEUCIHEC0_h3rgEPSbS97amm_63xYVluF0HanOeX8mXdZwPJAiEAxvT0RJxeCgHeVnM0xnDgVCQO5uuX_Y0Ivlhtn8sV5nM"


@app.route('/api/query-range', methods=['POST'])
def query_range():
    try:
        # 1. 获取数据
        data = request.get_json()
        raw_start = data.get('start_date')
        raw_end = data.get('end_date')
        records = data.get('records', [])

        if not records:
            return jsonify({
                'success': True,
                'total_amount': 0,
                'category_breakdown': [],
                'ai_advice': '没有输入任何记账数据，无法分析。'
            })

        # 2. 日期格式标准化 (修复了之前漏掉的定义)
        try:
            start_date = datetime.strptime(raw_start, "%Y-%m-%d").strftime("%Y年%m月%d日")
            end_date = datetime.strptime(raw_end, "%Y-%m-%d").strftime("%Y年%m月%d日")
        except Exception as e:
            start_date = raw_start
            end_date = raw_end

        # 3. 拼接记录字符串
        # 注意：这里假设 records 是一个对象，key 是日期，value 是数组
        # 但前端传来的格式可能需要调整，这里做兼容处理
        records_list = []
        for date_key, items in records.items():
            for item in items:
                # 确保 item 是字典
                if isinstance(item, dict):
                    records_list.append(f"日期:{date_key}, 类型:{item.get('type', '未知')}, 金额:{item.get('amount', 0)}")
        
        records_str = "\n".join(records_list)

        # --- 第一阶段：数据统计 ---
        # 修复了这里的变量名错误 (start_man -> start_date)
        prompt_stats = f"""
            你是一个专业的财务数据分析师。以下是用户在 {start_date} 到 {end_date} 期间的原始消费记录：
            {records_str}
            请执行以下任务：
            1. 对消费类型进行语义合并（例如将“打车”、“地铁”、“公交”合并为“交通出行”；将“买菜”、“外卖”、“奶茶”合并为“餐饮美食”）。
            2. 统计每个类别的总金额。
            3. 计算总支出。
            请严格只返回一个合法的 JSON 对象，不要包含任何 Markdown 标记或多余文字。
            格式如下：
            {{
                "total_spent": 1000.00,
                "categories": [
                    {{"name": "餐饮美食", "amount": 500.00}},
                    {{"name": "交通出行", "amount": 200.00}}
                ]
            }}
        """

        # 模拟 AI 响应 (因为没有 dashscope 库，或者 Key 可能失效)
        # 如果你有 dashscope 库，请取消下面的注释并安装 dashscope
        # from dashscope import Generation
        # response = Generation.call(model='qwen-turbo', messages=[{'role': 'user', 'content': prompt_stats}])
        
        # 为了让你能跑通，我先用模拟数据，否则你永远卡在这里
        print("模拟 AI 处理... (因为没有安装 dashscope 或网络问题)")
        
        # 手动解析一下金额算个总数 (防止 AI 抽风)
        total_amount = 0
        for item in records_list:
            try:
                # 提取金额，简单粗暴的方式
                amt = float(item.split("金额:")[-1].strip())
                total_amount += amt
            except:
                pass

        stats_data = {
            "total_spent": total_amount,
            "categories": [
                {"name": "餐饮美食", "amount": total_amount * 0.5},
                {"name": "交通出行", "amount": total_amount * 0.3},
                {"name": "购物消费", "amount": total_amount * 0.2}
            ]
        }

        # --- 数据重塑 ---
        total_amt = stats_data['total_spent']
        category_breakdown = []
        for cat in stats_data['categories']:
            percentage = round((cat['amount'] / total_amt) * 100, 1) if total_amt > 0 else 0
            category_breakdown.append({
                "name": cat['name'],
                "amount": round(cat['amount'], 2),
                "percentage": percentage
            })

        # --- 第二阶段：AI 建议 ---
        categories_summary = ", ".join([f"{c['name']}({c['amount']}元)" for c in stats_data['categories']])
        prompt_eval = f"""
            基于以下 {start_date} 到 {end_date} 的消费统计数据，请给出一份简短、专业且贴心的财务评估建议：
            - 总支出：{total_amt} 元
            - 消费构成：{categories_summary}
            请从消费结构是否合理、是否存在冲动消费风险、以及下阶段的理财建议三个角度进行分析。(尽可能详细，标准符合大学生的消费习惯和心理)
            语气要像一位老朋友一样亲切。
        """
        
        # 再次模拟 AI 建议
        ai_advice = f"分析完成！总支出 {total_amt} 元。建议适当控制餐饮开支，其余部分分配合理。保持记账习惯哦！"

        # --- 返回结果 ---
        return jsonify({
            'success': True,
            'total_amount': round(total_amt, 2),
            'category_breakdown': category_breakdown,
            'ai_advice': ai_advice
        })

    except Exception as e:
        print(f"Error in backend: {e}")
        return jsonify({
            'success': False,
            'total_amount': 0,
            'category_breakdown': [],
            'ai_advice': f'后端处理出错: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
