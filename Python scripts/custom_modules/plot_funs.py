import os
import folium
import io
import base64
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import plotly.express as px
from pathlib import Path
from PIL import Image, ImageDraw, ImageColor
from datetime import datetime
from modelling_funs import *

def plot_missing_rate(missing_rate, start_year, end_year, save_path, threshold=0.5, rewrite=True):
  """
  Plot the missing rate for sensors and save the figure.
  """
  if rewrite == True or not save_path.exists():
    missing_rate.plot(kind='bar', figsize=(30, 12))
    plt.ylabel('Ratio of Missing Values', fontsize=20)
    plt.tick_params(axis='x', labelsize=20)
    plt.tick_params(axis='y', labelsize=20)
    plt.title('Ratio of Missing Values per Sensor for {}-{}'.format(start_year, end_year), fontsize=18)

    # Adding a horizontal line at the threshold
    plt.axhline(y=threshold, color='r', linestyle='--', label=f"Threshold: {threshold}")
    plt.legend(fontsize=16)  # add legend to show threshold label

    save_path = os.path.join(save_path, f'missing_values_per_sensor_{start_year}_{end_year}.png')
    plt.savefig(save_path, bbox_inches='tight', pad_inches=0.1)
    plt.close()
    if Path(save_path).exists():
      print(f"{save_path} updated.")
    else:
      print(f"{save_path} saved.")
  else:
    if Path(save_path).exists():
      print(f"{save_path} exists and will not be updated.")

# plot whole sensors data in a same plot
def plot_time_series_data(df, start_year, end_year, save_path, title_prefix="Time Series of Sensor Hourly Counts", rewrite=True):
  """
  Plot the time series data for sensors and save the figure.
  """
  if rewrite == True or not save_path.exists():
    fig, ax = plt.subplots(figsize=(50, 20))

    for sensor in df.index:
      ax.plot(df.columns, df.loc[sensor], label=sensor)

    ax.set_title(f'{title_prefix} for {start_year}-{end_year}', fontsize=20)
    ax.set_ylabel('Hourly Counts', fontsize=20)
    ax.set_xlabel('Date and Time', fontsize=20)
    ax.tick_params(axis='x', labelsize=20)
    ax.tick_params(axis='y', labelsize=20)
    ax.legend(title='Sensor Name', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=20)

    save_path = os.path.join(save_path, f'time_series_data_{start_year}_{end_year}.png')
    plt.savefig(save_path, bbox_inches='tight', pad_inches=0.1)
    plt.close()

    if Path(save_path).exists():
      print(f"{save_path} updated.")
    else:
      print(f"{save_path} saved.")
  else:
    if Path(save_path).exists():
      print(f"{save_path} exists and will not be updated.")

def plot_time_series_data_sensor(df, start_year, end_year, 
                                 save_path, 
                                 title_prefix="Time Series of Sensor Hourly Counts", 
                                 agg=['raw', 'monthly'],
                                 with_shadow_missing=[False, True],
                                 fig_name='time_series_data_sensor',
                                 rewrite=True):
  """
  Plot the time series data for sensors and save the figure.
  the data should be provted (index are sensor_name and columns are data_time)
  """
  if rewrite == True or not save_path.exists():
    df.columns = pd.to_datetime(df.columns)
    print(df.shape)
    
    num_sensors = len(df.index)

    # Calculate number of rows and columns for a square-ish grid
    cols = int(np.ceil(np.sqrt(num_sensors)))
    rows = int(np.ceil(num_sensors / cols))

  for aggregation in agg:
    if aggregation == 'monthly':
      df_agg = df.transpose().resample('M').sum().transpose()  # Monthly aggregation
    else:
      df_agg = df

    for shade_missing in with_shadow_missing:
      fig, axes = plt.subplots(rows, cols, figsize=(40, 20), constrained_layout=True, sharex=True)
      print(rows, cols)

      if num_sensors == 1:
        axes = np.array([[axes]])

      for i, sensor in enumerate(df_agg.index):
        ax = axes[i // cols, i % cols]
        data = df_agg.loc[sensor]
        ax.plot(data.index, data, lw=1)
        title = sensor
        new_title = title.split('|')[-1] if '|' in title else title
        ax.set_title(new_title.strip(), fontsize=20)

        if shade_missing:
          if aggregation == 'raw':
            missing_data = pd.isna(data)
            if missing_data.any():
              start_dates = data.index[missing_data & ~missing_data.shift(1).fillna(False)]
              end_dates = data.index[missing_data & ~missing_data.shift(-1).fillna(False)]
              for start, end in zip(start_dates, end_dates):
                ax.add_patch(patches.Rectangle((start, ax.get_ylim()[0]), end - start, ax.get_ylim()[1] - ax.get_ylim()[0], fill=True, color='orange', alpha=0.2))
          else:
            missing_data_ratio = df.transpose().resample('M').apply(lambda x: x.isna().sum() / len(x)).transpose()
            to_shade = missing_data_ratio.loc[sensor] == 1.0
            for month, shade in zip(data.index, to_shade):
                if shade:
                    ax.add_patch(patches.Rectangle((month, ax.get_ylim()[0]), np.timedelta64(1, 'M'), ax.get_ylim()[1] - ax.get_ylim()[0], fill=True, color='orange', alpha=0.2))

        ax.tick_params(axis='y', labelsize=20)
        if i // cols != rows - 1:
          ax.tick_params(axis='x', which='both', bottom=False, top=False, labelbottom=False)
        else:
          ax.tick_params(axis='x', labelsize=20, rotation=90)
      for i in range(num_sensors, rows * cols):
        axes[i // cols, i % cols].axis('off')

      fig.suptitle(f'{title_prefix} for {start_year}-{end_year} ({aggregation})', fontsize=25)

      suffix = f'{aggregation}_with_shade' if shade_missing else f'{aggregation}_without_shade'
      final_path = os.path.join(save_path, f'{fig_name}_{start_year}_{end_year}_{suffix}.png')
      plt.savefig(final_path, bbox_inches='tight', pad_inches=0.1)
      plt.close()
    if Path(final_path).exists():
        print(f"{final_path} updated.")
    else:
      print(f"{final_path} saved.")
  else:
    if Path(save_path).exists(): # TBD
      print(f"{save_path} exists and will not be updated.")

def plot_time_series_data_iterative(df, save_path, start_year=None, end_year=None, aggregate_by_month=False, rewrite=True):
  if rewrite == True or not save_path.exists():
    df = df.copy()
    num_sensors = len(pd.unique(df['New_Sensor_Name']))
    cols = int(np.ceil(np.sqrt(num_sensors)))

    if aggregate_by_month:
      df.set_index('Date_Time', inplace=True)
      df = df.groupby('New_Sensor_Name').resample('M').sum(numeric_only=True).reset_index()
      df['Date_Time'] = df['Date_Time'].dt.to_period('M')
      df['Date_Time'] = df['Date_Time'].dt.strftime('%Y-%m')

    fig = px.line(df, x="Date_Time", y="Hourly_Counts", facet_col="New_Sensor_Name",
                  facet_col_wrap=cols,
                  facet_row_spacing=0.03, # default is 0.07 when facet_col_wrap is used
                  facet_col_spacing=0.03, # default is 0.03
                  height=1500, width=2000,
                  title="Time Series of Sensor Hourly Counts")
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_yaxes(showticklabels=True, matches=None)
    fig.update_layout(title_x=0.5)

    if start_year is None:
      save_name = 'time_series_data.html'
    else:
      if aggregate_by_month:
        save_name = f'time_series_data_sensor_{start_year}_{end_year}_monthly.html'
      else:
        save_name = f'time_series_data_sensor_{start_year}_{end_year}_raw.html'

    fig.write_html(os.path.join(save_path, save_name))

    if Path(save_path).exists():
        print(f"{save_path} updated.")
    else:
      print(f"{save_path} saved.")
  else:
    if Path(save_path).exists():
      print(f"{save_path} exists and will not be updated.")

def plot_best_k(df_scores, save_path):
  min_x = np.min(df_scores['Number_of_Clusters'])
  max_x = np.max(df_scores['Number_of_Clusters'])
  df_scores.sort_values(by='Number_of_Clusters', inplace=True)
  print(f"the number of clusters is from {min_x} to {max_x}")
  ss_scores = df_scores['Silhouette_Score'].values.tolist()
  distortions = df_scores['Distortion'].values.tolist()
  db_scores = df_scores['Davies_Bouldin'].values.tolist()
  ch_scores = df_scores['Calinski_Harabasz'].values.tolist()
  
  fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
  
  def plot_subplot(ax, scores, title, xlabel, ylabel, xytext_offset, is_higher_better=True, is_elbow=False):
    if is_elbow:
      optimal_k_index = find_elbow(scores)
    else:
      optimal_k_index = scores.index(max(scores)) if is_higher_better else scores.index(min(scores))
    
    optimal_k = df_scores['Number_of_Clusters'].iloc[optimal_k_index]
    score = scores[optimal_k_index]
    ax.plot(range(min_x, max_x+1), scores, marker='*' if is_higher_better else 'o')
    ax.axvline(x=optimal_k, color='r', linestyle='--')
    ax.set_xticks(range(min_x, max_x+1))
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    annotation = f"{'Max' if is_higher_better else 'Min'}: {optimal_k} ({round(score, 2)})"
    ax.annotate(annotation, 
                xy=(optimal_k, score), 
                xytext=(optimal_k + xytext_offset[0], score + xytext_offset[1]), 
                arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5))

  # Call plot_subplot for each subplot with specific parameters
  plot_subplot(ax1, ss_scores, 
               'The Silhouette Score showing the optimal k', 'Number of clusters', 'Silhouette Score', 
               (2, 0))
  plot_subplot(ax2, distortions, 
               'The Elbow Method showing the optimal k', 'Number of clusters', 'Distortion', 
               (2, 0), 
               is_higher_better=False, is_elbow=True)
  plot_subplot(ax3, db_scores, 
               'The Davies-Bouldin Index showing the optimal k', 'Number of clusters', 'Davies-Bouldin Index', 
               (2, 0), 
               is_higher_better=False)
  plot_subplot(ax4, ch_scores, 
               'The Calinski-Harabasz Index showing the optimal k', 'Number of clusters', 'Calinski-Harabasz Index', 
               (2, 0))
  
  plt.tight_layout()
  plt.subplots_adjust(hspace=0.3)
  plt.savefig(save_path / 'evaluation_metrics_plot.png', dpi=800, bbox_inches='tight', pad_inches=0.1)
  plt.show()

def plot_map(data, save_path):
  df = data.copy()

  # Group by Sensor_Name and Cluster
  try:
    grouped_df = df.groupby(['Sensor_Name', 'Clusters'])
  except:
    grouped_df = df.groupby(['New_Sensor_Name', 'Clusters'])

  # Create a map centered around the mean coordinates
  m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=13)

  # Define a list of colors (from the accepted color list)
  colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen']

  # Define a list of icon types
  icons = ['info-sign', 'cloud', 'star', 'heart', 'flag', 'euro', 'ok', 'remove-sign', 'flash', 'question-sign']

  # Loop through the groups (Sensor_Name and Cluster)
  for (sensor_name, cluster), group_data in grouped_df:
      # Take mean latitude and longitude
      lat = group_data['Latitude'].mean()
      long = group_data['Longitude'].mean()

      # Get the color and icon for this cluster
      color = colors[cluster % len(colors)]
      icon_type = icons[cluster // len(colors) % len(icons)]

      # Create the marker
      folium.Marker(
          [lat, long],
          popup=f"Sensor: {sensor_name}, Cluster: {cluster}",
          icon=folium.Icon(color=color, icon=icon_type, prefix='glyphicon')
      ).add_to(m)

  # Save the map
  m.save(save_path / 'map.html')
  print("map saved.")

def plot_pca_heatmap(pca, original_features, save_dir):
  components = pca.components_
  
  if components.shape[0] <= 20:
    plt.figure(figsize=(15, 8))
  else:
    plt.figure(figsize=(30, 12))
  sns.heatmap(components, 
              cmap='coolwarm', 
              yticklabels=[f"PC{i+1}" for i in range(components.shape[0])], 
              xticklabels=original_features,
              cbar_kws={"label": "Weight"})
  plt.title('PCA Component Weights by Sensor')
  # plt.tight_layout()
  plt.savefig(save_dir / 'plot_pca_heatmap.png', bbox_inches='tight')
  print('plot_pca_heatmap.png saved.')

def get_gradient_color(base_color, value, max_value):
  base_rgb = ImageColor.getcolor(base_color, "RGB")
  white_rgb = (255, 255, 255)
  factor = value / max_value
  gradient_rgb = tuple(int(white_rgb[i] * (1 - factor) + base_rgb[i] * factor) for i in range(3))
  return gradient_rgb

# def get_opacity(value, max_value):
#   return value / max_value

def get_opacity(value, max_value):
  min_opacity = 0.9
  max_opacity = 1.0
  scale_factor = (value / max_value) ** 0.3
  return min_opacity + (max_opacity - min_opacity) * scale_factor

def create_icon(gradient_color, opacity_value):
  image = Image.new('RGBA', (30, 30))
  draw = ImageDraw.Draw(image)
  # draw.ellipse([(0, 0), (30, 30)], fill=(*gradient_color, int(255 * opacity_value)))

  draw.ellipse([(0, 0), (30, 30)], outline="black", width=2)  # Added width=2 for a thicker border
  draw.ellipse([(2, 2), (28, 28)], fill=(*gradient_color, int(255 * opacity_value)))
  
  buffered = io.BytesIO()
  image.save(buffered, format="PNG")
  img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
  return f"data:image/png;base64,{img_str}"

def plot_map_gradient_color(data, save_path):
  df = data.copy()

  try:
    grouped_df = df.groupby(['Sensor_Name', 'Clusters'])
  except:
    grouped_df = df.groupby(['New_Sensor_Name', 'Clusters'])

  m = folium.Map(location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=15)
  m_png = folium.Map(width=1300, height=900, location=[df['Latitude'].mean(), df['Longitude'].mean()], zoom_start=15)

  # colors = [
  #   'red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 
  #   'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 
  #   'lightgreen', 'gray', 'black', 'lightgray'
  # ]

  colors = [
    'red', 'blue', 'green', 'purple', 'orange', 'pink', 'gray', 'darkred', 'white', 'beige', 
    'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'lightblue', 'lightred'
    'lightgreen','black', 'lightgray'
  ]

  latitudes = []
  longitudes = []

  for (sensor_name, cluster), group_data in grouped_df:
    df_subset = df[df['Clusters'] == cluster]
    group_max_value = df_subset['total_counts'].max()
    base_color = colors[cluster % len(colors)]

    for _, row in group_data.iterrows():
      lat = row['Latitude']
      long = row['Longitude']
      value = row['total_counts']
      gradient_color = get_gradient_color(base_color, value, group_max_value)
      opacity_value = get_opacity(value, group_max_value)
      icon_image = create_icon(gradient_color, opacity_value)

      # folium.CircleMarker(
      #     location=[lat, long],
      #     radius=12,
      #     popup=f"Sensor: {sensor_name}, Cluster: {cluster}, Counts: {value}",
      #     color=base_color,
      #     fill=True,
      #     fill_color=base_color,
      #     fill_opacity=opacity_value,
      # ).add_to(m)

      folium.Marker(
        [lat, long],
        popup=f"Sensor: {sensor_name}, Cluster: {cluster}, Counts: {value}",
        # icon=folium.Icon(color=base_color, icon='info-sign', prefix='glyphicon')
        icon=folium.CustomIcon(icon_image=icon_image, icon_size=(30, 30))
      ).add_to(m)

      folium.Marker(
        [lat, long],
        popup=f"Sensor: {sensor_name}, Cluster: {cluster}, Counts: {value}",
        # icon=folium.Icon(color=base_color, icon='info-sign', prefix='glyphicon')
        icon=folium.CustomIcon(icon_image=icon_image, icon_size=(30, 30))
      ).add_to(m_png)

      latitudes.append(lat)
      longitudes.append(long)

  m.fit_bounds([(min(latitudes), min(longitudes)), (max(latitudes), max(longitudes))])
  m_png.fit_bounds([(min(latitudes), min(longitudes)), (max(latitudes), max(longitudes))])
  m.save(str(save_path / 'map.html'))
  print("map.html saved.")

  img_data = m_png._to_png(5)
  img = Image.open(io.BytesIO(img_data))
  img.save(str(save_path / 'map.png'))
  print("map.png saved.")

if __name__ =='__main__':
  # df_scores = pd.read_excel('find_best_k.xlsx') 
  # plot_best_k(df_scores, './')

  clusters = pd.read_csv('../clusters_raw.csv') 
  clusters_ = clusters.drop(columns=['Latitude', 'Longitude', 'Clusters']).set_index('Sensor_Name')
  clusters['total_counts'] = clusters_.sum(axis=1).values
  plot_map_gradient_color(clusters, Path('../'))