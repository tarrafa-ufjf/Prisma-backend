from flask import request, jsonify, Flask

app = Flask(__name__)

tasks = []  # Lista para armazenar as tarefas
task_id_control = 1  # Controlador de IDs para garantir unicidade

@app.route("/tasks", methods=["POST"])
def create_task():
    global task_id_control
    data = request.get_json()  # Pega os dados enviados no corpo da requisição
    new_task = {
        "id": task_id_control,
        "title": data.get("title"),  # Obtém o título enviado
        "description": data.get("description", ""),  # Descrição opcional
        "completed": False  # Define que a tarefa começa como incompleta
    }
    tasks.append(new_task)  # Adiciona a nova tarefa à lista
    task_id_control += 1  # Incrementa o ID para a próxima tarefa
    return jsonify({"message": "Tarefa criada com sucesso!", "task": new_task}), 201

@app.route("/")
def hello():
    return "Hello, Flask + Poetry!"

if __name__ == '__main__':
    app.run(debug=True)