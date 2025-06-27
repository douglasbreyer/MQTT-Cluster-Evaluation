import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

# 1) MAPEAMENTO DAS PASTAS (ajuste o caminho do Random se necessário)
dirs = {
    'RoundRobin':  r"C:\Users\dougl\OneDrive\Área de Trabalho\HAPROXY - ROUNDROBIN\compilados",
    'Random':      r"C:\Users\dougl\OneDrive\Área de Trabalho\HAPROXY - RANDOM\compilados",       # <-- corrija este path se estiver diferente
    'LeastConn':   r"C:\Users\dougl\OneDrive\Área de Trabalho\HAPROXY- LEASTCON\compilados",
    'First':       r"C:\Users\dougl\OneDrive\Área de Trabalho\HAPROXY - FIRST\compilados",
}

output_dir = r"C:\Users\dougl\OneDrive\Área de Trabalho\GRAFICOS ANALISE"
os.makedirs(output_dir, exist_ok=True)

# 2) DEFINIÇÃO DAS MÉTRICAS E SUFIXOS PARA ARQUIVOS
metrics_info = {
    'Vazão média (throughput médio do publisher)':  ('vazao_publisher', 'Vazão Média do Publisher',      'Msgs/S'),
    'Vazão média (throughput médio do subscriber)': ('vazao_subscriber','Vazão Média do Subscriber',    'Msgs/S'),
    'Latência média':                               ('latencia_media',   'Latência Média',               'Ms'),
    '% médio de mensagens entregues':               ('perc_entregues',   'Porcentagem Mensagens Entregues','%'),
}

# 3) LEITURA E AGRUPAMENTO DOS DADOS
# data[(publicadores, mensagens)][metr][algoritmo][broker] = valor
data = defaultdict(lambda: {
    metr: {alg: {} for alg in dirs.keys()}
    for metr in metrics_info.keys()
})

for alg, folder in dirs.items():
    pattern = os.path.join(folder, "*-compilado.xlsx")
    for filepath in glob.glob(pattern):
        # extrai nome sem caminho e extensão
        fname = os.path.basename(filepath).replace("-compilado.xlsx","")
        parts = fname.split("_")
        if len(parts) != 4:
            # ignora arquivos com nome fora do padrão
            continue
        alg_key, pub_str, msg_str, broker_str = parts
        brokers = int(broker_str)
        scenario = (pub_str, msg_str)
        # lê planilha
        df = pd.read_excel(filepath)
        for metr_label in metrics_info:
            # pega o valor médio
            val = df.loc[df['Métrica'] == metr_label, 'Valor médio'].squeeze()
            data[scenario][metr_label][alg][brokers] = val

# 4) GERAÇÃO E SALVAMENTO DOS GRÁFICOS
for (pub, msg), mets in data.items():
    for metr_label, alg_dict in mets.items():
        suf, title, ylabel = metrics_info[metr_label]
        plt.figure(figsize=(6,4))
        for alg, brokermap in alg_dict.items():
            x = sorted(brokermap.keys())
            y = [brokermap[b] for b in x]
            plt.plot(x, y, marker='o', label=alg)
        plt.title(f"{title} ({pub} pubs · {msg} msgs)")
        plt.xlabel("Número de Brokers")
        plt.ylabel(ylabel)
        plt.xticks([1,2,3])
        plt.grid(True)
        plt.legend()
        # nome do arquivo: ex. "25_5000_vazao_publisher.png"
        out_name = f"{pub}_{msg}_{suf}.png"
        plt.savefig(os.path.join(output_dir, out_name), dpi=150, bbox_inches='tight')
        plt.close()

print("Todas as imagens foram salvas em:", output_dir)
