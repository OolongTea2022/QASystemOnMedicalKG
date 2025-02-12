from flask import Flask, request, jsonify

from chatbot_graph import * # 导入问答模块

app = Flask(__name__)


# ChatBotGraph
handler = ChatBotGraph()

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/query', methods=['POST'])
def query():
    data = request.json
    question = data.get('question', '')

    answer = handler.chat_main(question)
    
    return jsonify({
        'answer': answer
    })


if __name__ == '__main__':
    app.run(debug=True)
