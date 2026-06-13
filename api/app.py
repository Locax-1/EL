
# --- 基础库导入 ---
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from collections import defaultdict
import dashscope
from dashscope import Generation

# --- 配置区 ---
app = Flask(__name__)
CORS(app)  # 允许跨域
dashscope.api_key = "sk-ws-H.REDRMDY.JZ2P.MEUCIHEC0_h3rgEPSbS97amm_63xYVluF0HanOeX8mXdZwPJAiEAxvT0RJxeCgHeVnM0xnDgVCQO5uuX_Y0Ivlhtn8sV5nM"

# --- 路由定义 ---
@app.route('/api/query-range', methods=['POST'])
def query_range():
    data = request.json
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    records = data.get('records', [])
    
    if not records:
        return jsonify({'success': False, 'error': '没有可分析的数据'})

    try:
        # 1. 数据预处理：拼接字符串
        records_str = "\n".join([
            f"日期:{r['date']}, 类型:{r['type']}, 金额:{r['amount']}" 
            for r in records if r.get('amount') not in [None, '']
        ])
        
        # 2. 第一阶段：调用 AI 进行分类归一化与统计
        prompt_stats = f"""
        你是一个专业的财务数据分析师。以下是用户在 {start_date} 到 {end_date} 期间的原始消费记录：
        {records_str}
        
        请执行以下任务：
        1. 对消费类型进行语义合并（例如将“打车”、“地铁”、“公交”合并为“交通出行”；将“买菜”、“外卖”、“奶茶”合并为“餐饮美食”）。
        2. 统计每个类别的总金额。
        3. 计算总支出。
        
        请严格只返回一个合法的 JSON 对象，不要包含任何 Markdown 标记或多余文字。格式如下：
        {{
            "total_spent": 1000.00,
            "categories": [
                {{"name": "餐饮美食", "amount": 500.00}},
                {{"name": "交通出行", "amount": 200.00}}
            ]
        }}
        """
        
        response_stats = Generation.call(
            model='qwen-turbo',
            messages=[{'role': 'user', 'content': prompt_stats}],
            result_format='message'
        )
        
        if response_stats.status_code != 200:
            raise Exception(f"AI 调用失败: {response_stats.message}")
            
        content_stats = response_stats.output.choices[0].message.content
        # 清理 Markdown 代码块标记
        content_stats = re.sub(r'^```json\s*', '', content_stats).strip()
        content_stats = re.sub(r'\s*```$', '', content_stats).strip()
        stats_data = json.loads(content_stats)

        # 3. 数据重塑 (适配前端格式)
        total_amount = float(stats_data.get('total_spent', 0))
        
        # 安全计算分类占比 (防止除零)
        category_breakdown = {}  # 1. 改为字典
        for cat in stats_data.get('categories', []):
            cat_name = cat.get('name', '其他')
            cat_amount = float(cat.get('amount', 0))
            percentage = round((cat_amount / total_amount) * 100, 1) if total_amount > 0 else 0
            
            # 2. 改为字典赋值，Key 就是分类名称
            category_breakdown[cat_name] = {
                "amount": cat_amount,
                "percentage": percentage
            }

        # 4. 第二阶段：生成财务健康建议
        categories_summary = ", ".join([f"{c['name']}({c['amount']}元)" for c in category_breakdown])
        prompt_eval = f"""
        基于以下 {start_date} 到 {end_date} 的消费统计数据，请给出一份简短、专业且贴心的财务评估建议（建议尽量详细）：
        - 总支出：{total_amount} 元
        - 消费构成：{categories_summary}
        
        请从消费结构是否合理、是否存在冲动消费风险、以及下阶段的理财建议三个角度进行分析。
        语气要像一位老朋友一样亲切。
        """
        
        response_eval = Generation.call(
            model='qwen-turbo',
            messages=[{'role': 'user', 'content': prompt_eval}],
            result_format='message'
        )
        
        ai_advice = "AI 正在思考中..."
        if response_eval.status_code == 200:
            ai_advice = response_eval.output.choices[0].message.content

        # 5. 返回最终结果
        return jsonify({ 
            'success': True,
            'total_amount': total_amount,
            'category_breakdown': category_breakdown,
            'ai_advice': ai_advice
        })

    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {str(e)}")
        return jsonify({'success': False, 'error': 'AI 返回的数据格式错误，请重试'})
    except Exception as e:
        print(f"服务器内部错误: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# --- 程序入口 ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)

#sk-ws-H.REDRMDY.JZ2P.MEUCIHEC0_h3rgEPSbS97amm_63xYVluF0HanOeX8mXdZwPJAiEAxvT0RJxeCgHeVnM0xnDgVCQO5uuX_Y0Ivlhtn8sV5nM