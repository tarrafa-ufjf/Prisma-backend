from database import Database, DatabaseAdmin
from rabbit import RabbitMQAdmin
from src.analysis_lib.analysis.analysis import Analyzer
import json

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
    "global_analysis_cognitive": {
        "func": "general_cognitive_analysis",
        "status_index": 5,
    },
    "global_analysis_give_up": {
        "func": "general_give_up_analysis",
        "status_index": 6,
    }
}


class Worker:
    def __init__(self, rabbit_admin):
        self.rabbit_admin = rabbit_admin
        self.db_admin = DatabaseAdmin()
        self.analyzer = Analyzer()
    
    def select_indicator_analysis(self, analysis_type, connector, version, analysis_config):
        if analysis_type == "global_analysis_performance":
            return self.analyzer.general_performance_analysis(connector, version, analysis_config)
        elif analysis_type == "global_analysis_engagement":
            return self.analyzer.general_engagement_analysis(connector, version, analysis_config)
        elif analysis_type == "global_analysis_motivation":
            return self.analyzer.general_motivation_analysis(connector, version, analysis_config)
        elif analysis_type == "global_analysis_pedagogic":
            return self.analyzer.general_pedagogic_analysis(connector, version, analysis_config)
        elif analysis_type == "global_analysis_cognitive":
            return self.analyzer.general_cognitive_analysis(connector, version, analysis_config)
        elif analysis_type == "global_analysis_give_up":
            return self.analyzer.general_give_up_analysis(connector, version, analysis_config)
        else:
            raise ValueError(f"Tipo de análise desconhecido: {analysis_type}")

    def global_analysis(self, message):
        body = message["body"]
        analysis_type = body["type"]
        version = self.db_admin.get_version_in_database(1)
        message["version"] = version
        connector = conn.get_connection_with_config(body.get("db_inst_config"))

        if analysis_type not in ANALYSIS_MAP:
            raise ValueError(f"Tipo de análise desconhecido: {analysis_type}")

        config = body.get("db_inst_config") or body.get("db_config")
        entry = ANALYSIS_MAP[analysis_type]

        res = self.select_indicator_analysis(analysis_type, connector, version, body.get("analysis_config", {}))
        
        if res["processed"] != res["total"]:
            self.rabbit_admin.publish_message("tasks_to_process", {
                "name": f"user:{analysis_type}",
                "body": {
                    "type": analysis_type,
                    "db_inst_config": config,
                    "analysis_config": res
                },
                "version": version
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
            analysis_type == "global_analysis_motivation" or
            analysis_type == "global_analysis_cognitive" or
            analysis_type == "global_analysis_give_up"): 
            worker.global_analysis(message)
        else:
            print(f"[!] Tipo de análise desconhecido: {analysis_type}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    rabbit_admin.channel.basic_qos(prefetch_count=1)
    rabbit_admin.channel.basic_consume(queue='tasks_to_process', on_message_callback=callback)

    print(' [*] Aguardando mensagens. Para sair pressione CTRL+C')
    while True:
        # try:
        rabbit_admin.channel.start_consuming()
        # except Exception as e:
        #     print(f"Erro: {e}")

if __name__ == '__main__':
    print("Worker iniciado. Aguardando mensagens...")
    continuously_listen()
