from mapper.map import Mapper
import pandas as pd
from analysis.Engajamento.engagement import Engagement
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional

class Analyzer:
    def __init__(self):
        self.mapper = Mapper()
        self.global_engagement: Optional[object] = None

    #Função temporária, apenas para testes
    def get_moodle_version(self, connector):
        return self.mapper.get_moodle_version(connector)

    async def general_query(self, connector, version):
        self.global_engagement = await self.engagement_analysis(None, 'geral', version, connector)

    async def engagement_analysis(self, course_id, type_query, version, connector):
        engagement = Engagement(self.mapper)
        res = None

        if type_query == 'geral':
            arquivo = Path("data/engagement_global_analysis.csv")
            if arquivo.exists():
                if asyncio.iscoroutine(self.global_engagement):
                    print('------------------------------------------', flush=True)
                    print("Global engagement analysis already running, waiting for completion...", flush=True)
                    self.global_engagement = asyncio.create_task(self.global_engagement)
                    await self.global_engagement
                elif hasattr(self.global_engagement, "done") and not self.global_engagement.done():
                    print('------------------------------------------', flush=True)
                    print("Ok", flush=True)
                    await self.global_engagement
                elif hasattr(self.global_engagement, "result"):
                    print('------------------------------------------', flush=True)
                    print("Global engagement analysis already completed, reading results...", flush=True)
                    _ = self.global_engagement.result()
                res = pd.read_csv(arquivo, header=None, names=['course_id', 'num_posts_required', 'posts_required_label'])
            else:
                print('------------------------------------------', flush=True)
                print("No global engagement analysis found, running general analysis...", flush=True)
                engagement.general_analysis(connector, version)
                res = pd.read_csv(arquivo, header=None, names=['course_id', 'num_posts_required', 'posts_required_label'])
        elif type_query == 'usuario':
            pass
        elif type_query == 'course': 
            res = engagement.course_analysis(course_id, version, connector)

        return res