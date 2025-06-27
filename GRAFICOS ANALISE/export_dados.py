import os
import glob
import json
import pandas as pd

# ===== CONFIGURAÇÃO DAS PASTAS =====
dirs = {
    'RoundRobin': r"C:\Users\dougl\OneDrive\Área de Trabalho\HAPROXY - ROUNDROBIN\compilados",
    'Random':      r"C:\Users\dougl\OneDrive\Área de Trabalho\HAPROXY - RANDOM\compilados",
    'LeastConn':   r"C:\Users\dougl\OneDrive\Área de Trabalho\HAPROXY- LEASTCON\compilados",
    'First':       r"C:\Users\dougl\OneDrive\Área de Trabalho\HAPROXY - FIRST\compilados",
}

output_dir = r"C:\Users\dougl\OneDrive\Área de Trabalho\GRAFICOS ANALISE"
os.makedirs(output_dir, exist_ok=True)

# ===== DEFINIÇÃO DAS MÉTRICAS E SUFIXOS =====
metrics_info = {
    'Vazão média (throughput médio do publisher)':  ('vazao_publisher',  'Msgs/S'),
    'Vazão média (throughput médio do subscriber)': ('vazao_subscriber', 'Msgs/S'),
    'Latência média':                               ('latencia_media',   'Ms'),
    '% médio de mensagens entregues':               ('perc_entregues',   '%'),
}

# ===== LEITURA E ORGANIZAÇÃO DOS DADOS =====
# Estrutura: data[<scenario>][<algorithm>][<brokers>][<metric_suf>] = valor
data = {}

for alg, folder in dirs.items():
    pattern = os.path.join(folder, "*-compilado.xlsx")
    for filepath in glob.glob(pattern):
        fname = os.path.basename(filepath).replace("-compilado.xlsx", "")
        parts = fname.split("_")
        if len(parts) != 4:
            continue
        _, pub_str, msg_str, broker_str = parts
        scenario = f"{pub_str}_{msg_str}"
        brokers = int(broker_str)
        # inicializa dicionários
        data.setdefault(scenario, {}).setdefault(alg, {}).setdefault(brokers, {})
        # lê a planilha
        df = pd.read_excel(filepath)
        # extrai cada métrica
        for label, (suf, _) in metrics_info.items():
            val = df.loc[df['Métrica'] == label, 'Valor médio'].squeeze()
            data[scenario][alg][brokers][suf] = float(val)

# ===== SALVAÇÃO EM JSON =====
json_path = os.path.join(output_dir, "dados_mqtt.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# ===== SALVAÇÃO EM CSV =====
# flatten para tabela: cada linha = cenário + algoritmo + brokers + métricas
rows = []
for scenario, algs in data.items():
    pub_str, msg_str = scenario.split("_")
    for alg, brokers_map in algs.items():
        for b, mets in brokers_map.items():
            row = {
                "publicadores": int(pub_str),
                "mensagens":    int(msg_str),
                "algoritmo":    alg,
                "brokers":      b,
            }
            row.update(mets)
            rows.append(row)

df_out = pd.DataFrame(rows)
csv_path = os.path.join(output_dir, "dados_mqtt.csv")
df_out.to_csv(csv_path, index=False)

print("Exportação concluída:")
print(" - JSON:", json_path)
print(" - CSV :", csv_path)
