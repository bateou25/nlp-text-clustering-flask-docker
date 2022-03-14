from operator import index
import zipfile
import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans

from stemming.porter2 import stem

from flask import Flask, request, make_response, send_file
from flasgger import Swagger
from io import BytesIO
import time
import zipfile


app = Flask(__name__)   
swagger = Swagger(app) 
# localhost:8000/apidocs


def cleanse_text(text):
    """
    get stem of a given text or word
    """
    if not text:
        return text
    # remove whitespaces
    clean = ' '.join(text.split())
    # stemming
    stemmed_text = [stem(word) for word in clean.split()]

    return ' '.join(stemmed_text)


@app.route('/cluster', methods=['POST'])
def cluster():
    """File endpoint returning a text cluster
    ---
    parameters:
      - name: col
        in: query
        type: string
        required: true
        default: text1
      - name: dataset
        in: formData
        type: file
        required: true
    responses:
        200:
            description: "text"        
    """
    # read data
    data = pd.read_csv(request.files['dataset'])

    # if a user specified a column in the dataset, overwrite the default col
    unstructure = request.args.get('col') if 'col' in request.args else 'text'

    no_of_clusters = 2
    if 'no_of_clusters' in request.args: # if a user input a specific num of cluster
        no_of_clusters = int(request.args.get('no_of_clusters')) # overwrite the default num of cluster        

    #########################
    # Clean data
    # impute any missing values with a string
    data = data.fillna('NULL')
    # get stem
    data['clean_sum'] = data[unstructure].apply(cleanse_text)
    #########################
    # Vectorize or convert to word embeddings
    # instantiate a vectorizer, i.e., term-document matrix
    vectorizer = CountVectorizer(analyzer='word',
                                stop_words='english')
    # fit to the stemmed or cleaned column
    counts = vectorizer.fit_transform(data['clean_sum'])
    #########################
    # Apply KMeans clustering
    kmeans = KMeans(n_clusters=no_of_clusters)
    # fit on data and predict the clusters on the counts
    data['cluster_num'] = kmeans.fit_predict(counts)
    data = data.drop(['clean_sum'], axis=1)
    ########################
    # Prepare the Excel output
    # instantiate a binary file object
    output = BytesIO()
    # write data to Excel format
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    data.to_excel(writer, sheet_name='Clusters', 
                  encoding='utf-8', index=False)   
    ########################
    # Find top keywords from the Kmeans clusters
    clusters = []
    for i in range(np.shape(kmeans.cluster_centers_)[0]): # loop through the clusters
        # create a dataset that concatenates the feature names (vectorizer) and clusters
        data_cluster = pd.concat([pd.Series(vectorizer.get_feature_names()),
                                  pd.DataFrame(kmeans.cluster_centers_[i])],
                                  axis=1)
        # rename columns 
        data_cluster.columns = ['keywords','weights']  
        # sort weights by desc                                
        data_cluster = data_cluster.sort_values(by=['weights'], ascending=False) 
        # get the corresponding top 10 keywords into a list
        data_clust = data_cluster.head(10)['keywords'].tolist()
        # append to empty list
        clusters.append(data_clust)
    # create dataframe from the top 10 keywords list and write to Excel
    pd.DataFrame(clusters).to_excel(writer, sheet_name='Top_Keywords', encoding='utf-8')
    ########################
    # Final output with charts
    # pivot
    # create a table - with the cluster number and the number (size) of the cluster
    data_pivot = data.groupby(['cluster_num'], as_index=False).size()
    data_pivot.name = 'size'
    data_pivot = data_pivot.reset_index()
    data_pivot.to_excel(writer, sheet_name='Cluster_Report', 
                  encoding='utf-8', index=False)
    # create chart from the table
    workbook = writer.book
    worksheet = writer.sheets['Cluster_Report']
    chart = workbook.add_chart({'type': 'column'})
    chart.add_series({
            'values': '=Cluster_Report!$C$2:$C'+str(no_of_clusters+1)
            })
    worksheet.insert_chart('D2', chart)
    
    writer.save()   
                  
    # compress Excel into a zip file
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        names = ['cluster_output.xlsx']
        files = [output]
        for i in range(len(files)):
            data = zipfile.ZipInfo(names[i])
            # set server timing - e.g. for different timezones
            data.date_time = time.localtime(time.time())[:6]
            data.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(data, files[i].getvalue())
    memory_file.seek(0)
    ########################
    # Making the output downloadable
    response = make_response(send_file(memory_file, attachment_filename='cluster_output.zip',
                                       as_attachment=True))   
    response.headers['Access-Control-Allow-Origin'] = '*'
    
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)