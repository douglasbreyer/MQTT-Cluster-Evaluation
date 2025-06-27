import pandas as pd
import numpy as np
import os
import glob

def compile_mqtt_results(input_dir, output_dir):
    """
    Agrupa arquivos de resultados MQTT por cenário e gera planilhas compiladas com:
    - Vazão média e máxima do publisher (da série sec_*)
    - Vazão média e máxima do subscriber (da série sec_*)
    - Latência média e máxima
    - Número de publicações
    - Número total de mensagens recebidas pelos subscribers
    - % médio de mensagens entregues
    Além das especificações do cenário extraídas de cada arquivo.
    """
    os.makedirs(output_dir, exist_ok=True)
    raw_files = [
        f for f in glob.glob(os.path.join(input_dir, "*.xlsx"))
        if "compilado" not in os.path.basename(f).lower()
    ]
    
    # Agrupa arquivos por cenário (prefixo antes do "_<índice>.xlsx")
    scenarios = {}
    for fpath in raw_files:
        base = os.path.splitext(os.path.basename(fpath))[0]
        scenario = "_".join(base.split("_")[:-1])
        scenarios.setdefault(scenario, []).append(fpath)
    
    for scenario, files in scenarios.items():
        pub_sec_vals      = []
        sub_sec_vals      = []
        pub_max_per_run   = []
        sub_max_per_run   = []
        avg_latencies     = []
        max_latencies     = []
        pubs              = []
        subs_total        = []
        pct_deliv         = []

        # lê specs do primeiro arquivo para extrair algoritmo e contagens
        df0 = pd.read_excel(files[0], sheet_name="Results", header=None)
        # encontra a linha onde A == "algoritmo" (case-insensitive)
        mask_algo = df0.iloc[:,0].astype(str).str.strip().str.lower() == "algoritmo"
        if mask_algo.any():
            row_algo = df0.index[mask_algo][0] + 1
            algorithm = str(df0.iat[row_algo, 0]).strip()
        else:
            algorithm = "unknown"
        pub_count    = int(df0.iat[row_algo, 1])  # também pub_sub
        sub_count    = pub_count
        msgs_per_pub = int(df0.iat[row_algo, 2])
        broker_count = int(df0.iat[row_algo, 3])

        for fpath in files:
            df = pd.read_excel(fpath, sheet_name="Results", header=None)
            # Publisher per-second
            mask_pub = (
                df.iloc[:,0].astype(str).str.contains("per second throughput", case=False) &
                df.iloc[:,0].astype(str).str.contains("publisher", case=False)
            )
            if mask_pub.any():
                vals = df.loc[mask_pub, 1:].dropna(axis=1).astype(float).values.flatten().tolist()
                pub_sec_vals.extend(vals)
                pub_max_per_run.append(max(vals))
            # Subscriber per-second
            mask_sub = (
                df.iloc[:,0].astype(str).str.contains("per second throughput", case=False) &
                df.iloc[:,0].astype(str).str.contains("subscriber", case=False)
            )
            if mask_sub.any():
                vals = df.loc[mask_sub, 1:].dropna(axis=1).astype(float).values.flatten().tolist()
                sub_sec_vals.extend(vals)
                sub_max_per_run.append(max(vals))
            # Latências
            avg_latencies.append(float(df.iat[14,1]))
            max_latencies.append(float(df.iat[13,1]))
            # Publicações e entregas
            p = float(df.iat[10,1])
            t = float(df.iat[10,2])
            pubs.append(p)
            subs_total.append(t)
            pct_deliv.append(t / (p * sub_count) * 100)

        # Monta DataFrame de resumo
        metrics = [
            "Vazão média (throughput médio do publisher)",
            "Vazão máxima (throughput máximo do publisher)",
            "Vazão média (throughput médio do subscriber)",
            "Vazão máxima (throughput máximo do subscriber)",
            "Latência média",
            "Latência máxima",
            "Número de publicações",
            "Número total de mensagens dos subscribers",
            "% médio de mensagens entregues"
        ]
        means = [
            np.mean(pub_sec_vals),
            np.mean(pub_max_per_run),
            np.mean(sub_sec_vals),
            np.mean(sub_max_per_run),
            np.mean(avg_latencies),
            np.mean(max_latencies),
            np.mean(pubs),
            np.mean(subs_total),
            np.mean(pct_deliv)
        ]
        stds = [
            np.std(pub_sec_vals,   ddof=1),
            np.std(pub_max_per_run,ddof=1),
            np.std(sub_sec_vals,   ddof=1),
            np.std(sub_max_per_run,ddof=1),
            np.std(avg_latencies,  ddof=1),
            np.std(max_latencies,  ddof=1),
            np.std(pubs,           ddof=1),
            np.std(subs_total,     ddof=1),
            np.std(pct_deliv,      ddof=1)
        ]
        summary_df = pd.DataFrame({
            "Métrica": metrics,
            "Valor médio": means,
            "Desvio padrão": stds
        })

        # DataFrame de especificações
        specs_df = pd.DataFrame({
            "Especificação": [
                "Algoritmo de balanceamento",
                "Número de publishers",
                "Número de subscribers",
                "Mensagens por publisher",
                "Número de brokers"
            ],
            "Valor": [
                algorithm, pub_count, sub_count, msgs_per_pub, broker_count
            ]
        })

        # Salva com nome completo do algoritmo
        out_name = f"{algorithm}_{pub_count}_{msgs_per_pub}_{broker_count}-compilado.xlsx"
        out_path = os.path.join(output_dir, out_name)
        with pd.ExcelWriter(out_path) as writer:
            summary_df.to_excel(writer, sheet_name="Resumo", index=False)
            specs_df.to_excel(writer, sheet_name="Especificacoes", index=False)
        print(f"[OK] {out_path}")

if __name__ == "__main__":
    # Exemplos de caminhos ABSOLUTOS no Windows
    input_dir  = r"C:\Users\dougl\OneDrive\Área de Trabalho\NGINX - LEASTCON"
    output_dir = r"C:\Users\dougl\OneDrive\Área de Trabalho\NGINX - LEASTCON\compilados"
    compile_mqtt_results(input_dir, output_dir)