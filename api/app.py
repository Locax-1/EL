from flask import Flask, request, jsonify
from flask_cors import CORS
from collections import defaultdict
import dashscope
from dashscope import Generation

app = Flask(__name__)
CORS(app)  # 允许跨域
from collections import defaultdict
import dashscope
from dashscope import Generation

app = Flask(__name__)

# 设置你的 API Key（请替换成你自己的 Key）
dashscope.api_key = "sk-ws-H.REDRMDY.JZ2P.MEUCIHEC0_h3rgEPSbS97amm_63xYVluF0HanOeX8mXdZwPJAiEAxvT0RJxeCgHeVnM0xnDgVCQO5uuX_Y0Ivlhtn8sV5nM"

@app.route('/api/ai-evaluate', methods=['POST'])
def ai_evaluate():
    data = request.json
    records = data.get('records', [])
    time_range = data.get('time_range', '未知时间段')

    # 1. 格式化前端传来的数据为文本
    # 这一步非常重要，要把 JSON 转成通义千问能读懂的自然语言
    record_text = ""
    for record in records:
        record_text += f"日期:{record['date']}, 类型:{record['type']}, 金额:{record['amount']}元\n"
    
    # 2. 构建 Prompt（提示词）
    # 这里的提示词决定了 AI 的回答质量
    prompt = f"""
    你是一位专业的财务分析师。请根据用户在 {time_range} 的消费记录，进行深度分析。
    要求：
    1. 计算总支出。
    2. 分析消费结构（如餐饮、交通占比）。
    3. 指出不合理的消费（如单笔过大、非必要支出）。
    4. 给出3条具体的省钱建议。
    
    消费记录如下：
    {record_text}
    """

    try:
        # 3. 调用通义千问模型
        # 这里使用 qwen-max 模型，效果较好
        response = Generation.call(
            model='qwen-max',
            prompt=prompt
        )
        
        # 4. 返回 AI 的分析结果
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'analysis': response.output.text
            })
        else:
            return jsonify({
                'success': False,
                'error': 'AI 分析失败: ' + str(response.code)
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
# 新增一个查询区间消费的接口
@app.route('/api/query-range', methods=['POST'])
def query_range():
    data = request.json
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    records = data.get('records', [])
    
    # 1. 使用字典进行同类型合并计算
    category_stats = defaultdict(float)
    total_amount = 0.0
    
    for record in records:
        category = record.get('type', '未分类')
        amount = record.get('amount', 0.0)
        category_stats[category] += amount
        total_amount += amount
    
    # 2. 按照金额从大到小排序
    sorted_categories = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
    
    # 3. 格式化输出文本
    summary_text = f"📅 统计周期：{start_date} 至 {end_date}\n"
    summary_text += f"💰 总消费金额：¥{total_amount:.2f}\n\n"
    summary_text += "📊 各分类明细：\n"
    
    for cat, amt in sorted_categories:
        # 计算占比
        percentage = (amt / total_amount * 100) if total_amount > 0 else 0
        summary_text += f"- {cat}: ¥{amt:.2f} ({percentage:.1f}%)\n"
        
    return jsonify({
        'success': True,
        'summary': summary_text
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)