import pandas as pd
import pypsa as py
import matplotlib.pyplot as plt
import numpy as np

df_ha = pd.read_csv('data/wind_hamburg_80m.csv')
df_da=pd.read_csv('data/pv_da.csv')
df_w_dd = pd.read_csv('data/wind_dd.csv')
df_pv_dd = pd.read_csv('data/pv_dd.csv')
df_price = pd.read_csv('data/epex_de_2019_hourly.csv')


df_price['time'] = pd.to_datetime(df_price['time'])
df_price['price'] = pd.to_numeric(df_price['price_eur_mwh'])

for df in [df_ha, df_da, df_w_dd, df_pv_dd]:
    df['time'] = pd.to_datetime(df['time'])
    df['el'] = pd.to_numeric(df['electricity'])

wind_ha = round(df_ha['el']/2000,2)
pv_da = round(df_da['el']/2000,2)
pv_dd = round(df_pv_dd['el']/1000,2)
wind_dd = round(df_w_dd['el']/1000,2)

n = py.Network()
n.set_snapshots(df_ha['time'].iloc[:8760])

#Hamburg
n.add('Bus','Hamburg')
n.add('Generator','Wind_HA',
      bus = 'Hamburg',
      p_nom = 2.0,
      marginal_cost = 0.00001,
      p_max_pu = wind_ha[:8760].values
      )
n.add('Load','HA',
      bus = 'Hamburg',
      p_set = 1.2
      )

#Darmstadt

n.add('Bus','Darmstadt')
n.add('Generator','PV_DA',
      bus = 'Darmstadt',
      p_nom = 2.0,
      p_max_pu = pv_da[:8760].values,
      marginal_cost = 0.00001
      )
n.add('StorageUnit','Battery_DA',
      bus = 'Darmstadt',
      p_nom = 5.0,
      max_hours = 4.0
      )
n.add('Load','DA',
      bus = 'Darmstadt',
      p_set = 0.6
      )

#Dresden

n.add('Bus','Dresden')
n.add('Generator','PV_DD',
      bus = 'Dresden',
      p_nom = 1.0,
      marginal_cost = 0.00001,
      p_max_pu = pv_dd[:8760].values
      )
n.add('Generator','Wind_DD',
      bus = 'Dresden',
      p_nom = 1.0,
      marginal_cost = 0.00001,
      p_max_pu = wind_dd[:8760].values
      )
n.add('Load','DD',
      bus = 'Dresden',
      p_set = 0.9
      )

#Gas Plant
n.add('Bus','GasPlant')
n.add('Generator','Gas',
      bus = 'GasPlant',
      p_nom = 3.0,
      marginal_cost = 50.0
      )

#Import
n.add('Bus','GridImport')
n.add('Generator','Import',
      bus = 'GridImport',
      p_nom = 3.0,
      marginal_cost = df_price['price'].iloc[:8760].values
      )

#Links
n.add('Link','HA-DA',
      bus0 = 'Hamburg',
      bus1 = 'Darmstadt',
      p_nom = 0.5,
      p_min_pu = -1.0,
      efficiency = 0.98,
      marginal_cost=0.00001
      )

n.add('Link','HA-DD',
      bus0 = 'Hamburg',
      bus1 = 'Dresden',
      p_nom = 0.5,
      p_min_pu = -1.0,
      efficiency = 0.98,
      marginal_cost=0.00001
      )

n.add('Link','DA-DD',
      bus0 ='Darmstadt',
      bus1 = 'Dresden',
      p_nom = 0.5,
      p_min_pu = -1.0,
      efficiency = 0.98,
      marginal_cost=0.00001
      )

n.add('Link', 'Gas-HA',
      bus0='GasPlant',
      bus1='Hamburg',
      p_nom=1.0,
      p_min_pu=0.0,
      efficiency=0.98,
      marginal_cost=0.00001
      )

n.add('Link', 'Gas-DA',
      bus0='GasPlant',
      bus1='Darmstadt',
      p_nom=1.0,
      p_min_pu=0.0,
      efficiency=0.98,
      marginal_cost=0.00001
      )

n.add('Link', 'Gas-DD',
      bus0='GasPlant',
      bus1='Dresden',
      p_nom=1.0,
      p_min_pu=0.0,
      efficiency=0.98,
      marginal_cost=0.00001
      )

n.add('Link', 'Import-HA',
      bus0 = 'GridImport',
      bus1 = 'Hamburg',
      p_nom = 1.0,
      p_min_pu = 0.0,
      efficiency = 0.98,
      marginal_cost=0.00001
      )

n.add('Link', 'Import-DA',
      bus0 = 'GridImport',
      bus1 = 'Darmstadt',
      p_nom = 1.0,
      p_min_pu = 0.0,
      efficiency = 0.98,
      marginal_cost=0.00001
      )

n.add('Link', 'Import-DD',
      bus0 = 'GridImport',
      bus1 = 'Dresden',
      p_nom = 1.0,
      p_min_pu = 0.0,
      efficiency = 0.98,
      marginal_cost=0.00001
      )

n.optimize(solver_name = 'highs')

prod = []
links = []

for i in ['Wind_HA','PV_DA','PV_DD','Wind_DD','Gas']:
        prod.append(n.generators_t.p[i])

for i in ['HA-DA','HA-DD','DA-DD','Gas-HA','Gas-DA','Gas-DD','Import-HA','Import-DA','Import-DD']:
        links.append(n.links_t.p0[i])


battery = n.storage_units_t.p['Battery_DA']

monthly_prod = []
monthly_links = []

for i in prod:
     monthly_prod.append(round(i.groupby(i.index.month).sum(),2))

for i in links:
     monthly_links.append(round(i.groupby(i.index.month).sum(),2))

monthly_bat = round(battery.groupby(battery.index.month).sum(),2)

avg_links = []

for i in links:
    avg_links.append(round(i.mean(),2))

print(avg_links)

prod_ha = round(monthly_prod[0].sum(),2)
prod_da = round(monthly_prod[1].sum(),2)
prod_dd =round(monthly_prod[2].sum() + monthly_prod[3].sum(),2)
prod_gas = round(monthly_prod[4].sum(),2)

# Import-Erzeugung monatlich
prod_import = n.generators_t.p['Import']
monthly_import = round(prod_import.groupby(prod_import.index.month).sum(), 2)

# Nettofluss pro Stadt (positiv = Import , negativ = Export)
net_ha = monthly_links[0] * (-1) + monthly_links[3] + monthly_links[6]  # -HA-DA + Gas-HA + Import-HA
net_da = monthly_links[0] + monthly_links[2] * (-1) + monthly_links[4] + monthly_links[7]  # HA-DA - DA-DD + Gas-DA + Import-DA
net_dd = monthly_links[1] + monthly_links[2] + monthly_links[5] + monthly_links[8]  # HA-DD + DA-DD + Gas-DD + Import-DD

# Kosten nach Quelle
gas_cost_monthly = monthly_prod[4] * 50
prod_import_by_month_price = (prod_import * df_price['price'].iloc[:8760].values)
import_cost_monthly = round(prod_import_by_month_price.groupby(prod_import_by_month_price.index.month).sum(), 2)

#Visualisierung

# --- 1. Monthly generation bar chart: Wind HH / PV DA / PV+Wind DR / Gas ---
df_prod_monthly = pd.DataFrame({
    'Wind Hamburg (HA)': monthly_prod[0],
    'PV Darmstadt (DA)': monthly_prod[1],
    'Dresden (PV + Wind)': monthly_prod[2] + monthly_prod[3],
    'Gaskraftwerk': monthly_prod[4]
})

df_links_monthly = pd.DataFrame({
    'HA-DA': monthly_links[0],
    'HA-DD': monthly_links[1],
    'DA-DD': monthly_links[2],
    'Gas-HA': monthly_links[3],
    'Gas-DA': monthly_links[4],
    'Gas-DD': monthly_links[5],
    'Import-HA': monthly_links[6],
    'Import-DA': monthly_links[7],
    'Import-DD': monthly_links[8],
})

months = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']

fig, ax1 = plt.subplots(figsize=(14, 7))
df_prod_monthly.plot(kind='bar', ax=ax1, width=0.8, edgecolor='black', alpha=0.85)
ax1.set_title('Monatliche Stromerzeugung nach Städten und Kraftwerken', fontsize=14, fontweight='bold', pad=15)
ax1.set_xlabel('Monat', fontsize=12)
ax1.set_ylabel('Erzeugung [MWh]', fontsize=12)
ax1.set_xticklabels(months, rotation=0)
ax1.grid(axis='y', linestyle='--', alpha=0.5)
ax1.legend(title="Kraftwerke/Städte", bbox_to_anchor=(1.02, 1), loc='upper left')

for container in ax1.containers:
    labels = [f'{val:.1f}' if val > 0.1 else '' for val in container.datavalues]
    ax1.bar_label(container, labels=labels, label_type='edge', fontsize=8, padding=3, rotation=90)

plt.tight_layout()


# --- 2. Battery Darmstadt state-of-charge time series (Winter + Sommerwoche) ---
soc = n.storage_units_t.state_of_charge['Battery_DA']

winter_week = soc.loc['2019-01-14':'2019-01-20']
summer_week = soc.loc['2019-07-15':'2019-07-21']

fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharey=True)

axes[0].plot(winter_week.index, winter_week.values, color='tab:blue')
axes[0].set_title('Battery Darmstadt SOC — Winterwoche (14.–20. Januar)')
axes[0].set_ylabel('State of Charge (MWh)')
axes[0].grid(True, alpha=0.3)

axes[1].plot(summer_week.index, summer_week.values, color='tab:orange')
axes[1].set_title('Battery Darmstadt SOC — Sommerwoche (15.–21. Juli)')
axes[1].set_ylabel('State of Charge (MWh)')
axes[1].set_xlabel('Zeit')
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('results/battery_soc.png', dpi=150)
plt.show()


# --- 3. Netzwerkdiagramm der mittleren Leistungsflüsse ---

link_names = [
    'HA-DA', 'HA-DD', 'DA-DD',
    'Gas-HA', 'Gas-DA', 'Gas-DD',
    'Import-HA', 'Import-DA', 'Import-DD'
]

avg_flows = dict(zip(link_names, avg_links))

node_pos = {
    'GasPlant': (0, 2),
    'Import': (0, -2),
    'Hamburg': (3, 3),
    'Darmstadt': (3.5, 0),
    'Dresden': (2.5, -3),
}

edges = [
    ('Gas-HA', 'GasPlant', 'Hamburg'),
    ('Gas-DA', 'GasPlant', 'Darmstadt'),
    ('Gas-DD', 'GasPlant', 'Dresden'),
    ('Import-HA', 'Import', 'Hamburg'),
    ('Import-DA', 'Import', 'Darmstadt'),
    ('Import-DD', 'Import', 'Dresden'),
    ('HA-DA', 'Hamburg', 'Darmstadt'),
    ('HA-DD', 'Hamburg', 'Dresden'),
    ('DA-DD', 'Darmstadt', 'Dresden'),
]

fig, ax = plt.subplots(figsize=(11, 8))

node_colors = {'GasPlant': 'lightcoral', 'GridImport': 'khaki'}

for node, (px, py) in node_pos.items():
    ax.scatter(
        px, py, s=2200,
        color=node_colors.get(node, 'lightsteelblue'),
        edgecolors='black', linewidth=1.5, zorder=3
    )
    ax.text(
        px, py, node,
        ha='center', va='center', fontsize=10, fontweight='bold', zorder=4
    )

max_flow = max(abs(v) for v in avg_flows.values())

# Leitungen zeichnen
for link_name, start, end in edges:
    flow = avg_flows[link_name]

    # Richtung umkehren
    if flow < 0:
        start, end = end, start
        flow = abs(flow)

    x0, y0 = node_pos[start]
    x1, y1 = node_pos[end]

    linewidth = 1 + 8 * flow / max_flow

    ax.annotate(
        '', xy=(x1, y1), xytext=(x0, y0),
        arrowprops=dict(
            arrowstyle='-|>', lw=linewidth, color='tab:blue',
            alpha=0.8, shrinkA=28, shrinkB=28
        )
    )

    ax.text(
        (x0 + x1) / 2, (y0 + y1) / 2, f'{flow:.2f} MW',
        fontsize=9, ha='center', va='center',
        bbox=dict(
            facecolor='white', edgecolor='gray', alpha=0.9,
            boxstyle='round,pad=0.25'
        )
    )

ax.set_xlim(-1, 4.5)
ax.set_ylim(-4, 4)
ax.axis('off')

ax.set_title(
    'Mittlere Leistungsflüsse im Netzwerk (2019)',
    fontsize=15, fontweight='bold'
)

plt.tight_layout()
plt.savefig('results/network_flow_diagram.png', dpi=300)
plt.show()


# --- 4. Link utilization bar chart ---
link_labels = ['Gas→HA','Gas→DA','Gas→DD','HA↔DA','HA↔DD','DA↔DD','Import→HA','Import→DA','Import→DD']

p_noms = [0.5, 0.5, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
order_labels = ['HA↔DA','HA↔DD','DA↔DD','Gas→HA','Gas→DA','Gas→DD','Import→HA','Import→DA','Import→DD']

utilization = []
for series, p_nom in zip(links, p_noms):
    avg_abs = series.abs().mean()
    utilization.append(round(100 * avg_abs / p_nom, 1))

fig, ax = plt.subplots(figsize=(12, 6))
bars = ax.bar(order_labels, utilization, color='seagreen')
ax.set_ylabel('Utilization (%)')
ax.set_title('Link Utilization — Durchschnittliche Auslastung')
ax.bar_label(bars, fmt='%.1f%%')
plt.xticks(rotation=30, ha='right')
plt.tight_layout()
plt.savefig('results/link_utilization.png', dpi=150)
plt.show()

#Tabellen

total_load_all = (n.loads.p_set['HA'] + n.loads.p_set['DA'] + n.loads.p_set['DD']) * len(n.snapshots)

total_gas_cost_keur = (prod_gas * 50) / 1000

summary_data = {
    'Kennzahl (Indikator)': [
        'Wind Hamburg — total ',
        'PV Darmstadt — total ',
        'PV+Wind Dresden — total ',
        'Gas — total ',
        'Total load (All cities)',
        'Total gas cost'
    ],
    'Wert': [
        prod_ha,
        prod_da,
        prod_dd,
        prod_gas,
        round(total_load_all, 2),
        round(total_gas_cost_keur, 2)
    ],
    'Einheit': ['MWh', 'MWh', 'MWh', 'MWh', 'MWh', 'K€']
}

df_summary = pd.DataFrame(summary_data)

df_summary.to_csv('results/summary_results.csv', index=False)

print("\n" + "="*60)
print("ZUSAMMENFASSUNG DER ERGEBNISSE (2019)")
print("="*60)
print(df_summary.to_string(index=False))
print("="*60)