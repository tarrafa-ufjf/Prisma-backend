from database import Database, DatabaseAdmin
from worker.rabbit import RabbitMQAdmin
import json
import requests

conn = Database()
connector = None


ANALYSIS_MAP = {
    "global_analysis_performance": {
        "func": "general_performance_analysis",
        "status_index": 2,
    },
    "global_analysis_engagement": {
        "func": "general_engagement_analysis",
        "status_index": 1,
    },
    "global_analysis_motivation": {
        "func": "general_motivation_analysis",
        "status_index": 3,
    },
    "global_analysis_pedagogic": {
        "func": "general_pedagogic_analysis",
        "status_index": 4,
    },
}


class Worker:
    def __init__(self, rabbit_admin):
        self.rabbit_admin = rabbit_admin
        self.db_admin = DatabaseAdmin()

    def global_analysis(self, message):
        global connector, version, analyzer

        body = message["body"]
        analysis_type = body["type"]

        if analysis_type not in ANALYSIS_MAP:
            raise ValueError(f"Tipo de análise desconhecido: {analysis_type}")

        config = body.get("db_inst_config") or body.get("db_config")

        if connector is None:
            connector = conn.get_connection_with_config(config)
        if version is None:
            version = body["version"]

        entry = ANALYSIS_MAP[analysis_type]
        res = requests.put(
            "http://localhost:5000/analysis/start",
            json={
                "type": analysis_type,
                "db_inst_config": config,
                "version": version
            }).json()
        
        if res["processed"] != res["total"]:
            self.rabbit_admin.publish_message("tasks_to_process", {
                "name": f"user:{analysis_type}",
                "version": message["version"],
                "body": {
                    "type": analysis_type,
                    "db_inst_config": config,
                    "analysis_config": res
                }
            }, priority=0)
        else:
            self.db_admin.update_global_analysis_status(1, entry["status_index"], 'D')

def continuously_listen():
    rabbit_admin = RabbitMQAdmin()

    def callback(ch, method, properties, body):
        message = json.loads(body.decode())
        analysis_type = message.get("body").get("type")
        worker = Worker(rabbit_admin)

        if (analysis_type == "global_analysis_engagement" or
            analysis_type == "global_analysis_pedagogic" or
            analysis_type == "global_analysis_performance" or
            analysis_type == "global_analysis_motivation"):
            worker.global_analysis(message)
        else:
            print(f"[!] Tipo de análise desconhecido: {analysis_type}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    rabbit_admin.channel.basic_qos(prefetch_count=1)
    rabbit_admin.channel.basic_consume(queue='tasks_to_process', on_message_callback=callback)

    print(' [*] Aguardando mensagens. Para sair pressione CTRL+C')
    while True:
        try:
            rabbit_admin.channel.start_consuming()
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == '__main__':
    print("Worker iniciado. Aguardando mensagens...")
    continuously_listen()
