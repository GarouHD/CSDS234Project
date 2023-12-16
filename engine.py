from pymongo import MongoClient
import networkx as nx
import matplotlib.pyplot as plt

# Connect to MongoDB
connection_string = 'REPLACE ME'
client = MongoClient(connection_string)
db = client['YoutubeData']
collection = db['Videos']


def find_videos(video_id=None, uploader=None, age=None, category=None, length=None,
                views=None, rate=None, ratings=None, comments=None):
    """
    Queries for videos with specified criteria, supporting both exact and ranged values.
    Parameters can be single values (for exact match) or tuples (for ranged queries).
    For example, age=(20, 30) will search for videos where age is between 20 and 30,
    while age = 30 will search for videos where age is exactly 30. Use float('inf')
    and float('inf') if you want '<' or '>'.
    Parameters not specified or set to None are not included in the query.
    """
    func_args = locals().items()
    query = {}

    # Builds query to find videos
    for key, value in func_args:
        if value is not None:
            if isinstance(value, tuple):
                # Handle range queries
                if value[0] == float('-inf'):
                    query[key] = {"$lt": value[1]}
                elif value[1] == float('inf'):
                    query[key] = {"$gt": value[0]}
                else:
                    query[key] = {"$gte": value[0], "$lte": value[1]}
            else:
                # Handle exact match
                query[key] = value

    documents = collection.find(query)

    doc_list = [doc for doc in documents]
    doc_dic = {doc['video_id']: doc for doc in doc_list}

    return doc_list, doc_dic


def frequency_by_attr(video_lis, attr, buckets=None):
    """
    Counts the frequency of videos by given attribute. For numerical attributes, must
    provide buckets of ranges you'd like to count. For example if attr = views and
    buckets = [0,1000,2000,3000] will count the number of videos with views between
    [0-1000],[1000-2000],[2000-3000] and [3000-inf]
    """

    stats = {}
    if attr in ['uploader', 'category']:
        for video in video_lis:
            attr_val = video[attr]
            if attr_val in stats:
                stats[attr_val] +=1
            else:
                stats[attr_val] = 1

    elif attr in ['age', 'length', 'views', 'rate', 'ratings', 'comments']:

        if buckets is None:
            print("No ranges provided")
            return stats

        values = [video[attr] for video in video_lis]

        # Initialize stats with bucket ranges
        for i in range(len(buckets)):
            if i == len(buckets) - 1:
                bucket_label = f"[{buckets[i]}-inf]"
            else:
                bucket_label = f"[{buckets[i]}-{buckets[i + 1]}]"
            stats[bucket_label] = 0

        # Assign values to buckets
        for val in values:
            for i in range(len(buckets)):
                if i == len(buckets) - 1:
                    if val >= buckets[i]:
                        bucket_label = f"[{buckets[i]}-inf]"
                        stats[bucket_label] += 1
                elif buckets[i] <= val < buckets[i + 1]:
                    bucket_label = f"[{buckets[i]}-{buckets[i + 1]}]"
                    stats[bucket_label] += 1
                    break # Correct bucket found, break
    else:
        print("Error: Invalid attribute ")

    print(stats)


def create_graph(video_lis, video_dic=None):
    """
    Creates a directed graph from a given list of videos. Each node is video_id with
    edges to related video ids. If video_dic is given, related_ids not in video_dic
    will not be added to the graph
    """
    G = nx.DiGraph()

    if video_dic is None:
        for video in video_lis:
            video_id = video['video_id']
            for related_id in video['related_ids']:
                G.add_edge(video_id, related_id)
    else:
        for video in video_lis:
            video_id = video['video_id']
            G.add_node(video_id)
            for related_id in video['related_ids']:
                if related_id in video_dic:
                    G.add_edge(video_id, related_id)

    return G


def degree_info(G):
    """
    Calculates the average, min, max degree, in-degree, out_degree of a given graph or
    subgraph of the Youtube Data.
    """

    in_degrees = [d for n, d in G.in_degree()]
    out_degrees = [d for n, d in G.out_degree()]
    degrees = [d for n, d in G.degree()]

    # Calculate average, min, and max for degrees, in-degrees and out-degrees
    avg_degree = sum(degrees) / len(degrees)
    min_degree = min(degrees)
    max_degree = max(degrees)

    avg_in_degree = sum(in_degrees) / len(in_degrees)
    min_in_degree = min(in_degrees)
    max_in_degree = max(in_degrees)

    avg_out_degree = sum(out_degrees) / len(out_degrees)
    min_out_degree = min(out_degrees)
    max_out_degree = max(out_degrees)

    print(f"Average Degree: {avg_degree}")
    print(f"Minimum Degree: {min_degree}")
    print(f"Maximum Degree: {max_degree}")
    print()

    print(f"Average In-Degree: {avg_in_degree}")
    print(f"Minimum In-Degree: {min_in_degree}")
    print(f"Maximum In-Degree: {max_in_degree}")
    print()

    print(f"Average Out-Degree: {avg_out_degree}")
    print(f"Minimum Out-Degree: {min_out_degree}")
    print(f"Maximum Out-Degree: {max_out_degree}")


def pagerank(G, k, video_dic):
    """
    Calculates the Page Rank scores of a given graph or subgraph and returns the top
    k the highest scores, in this case the top k most influential videos.
    """
    # Calculate PageRank scores
    pagerank_scores = nx.pagerank(G)

    # Sort nodes by PageRank score and get the top k
    top_k_nodes = sorted(pagerank_scores, key=pagerank_scores.get, reverse=True)[:k]

    count = 1
    for node in top_k_nodes:
        print(f"{count}: Video ID: {node} | PageRank Score: {pagerank_scores[node]}")
        if node in video_dic:
            print(video_dic[node])
        else:
            print('Video data not in database')
        count += 1
        print()

    return top_k_nodes


def save_graph(G):
    """
    Saves given graph as a .gexf file
    """
    nx.write_gexf(G, "graph.gexf")


def plot_attribute(video_lis, attr):
    """
    Plot the frequency of a given attribute
    """
    if attr not in ['age', 'length', 'views', 'rate', 'ratings', 'comments','uploader', 'category']:
        print("Invalid Attribute")
        return

    values = [video[attr] for video in video_lis]

    if isinstance(values[0], (int, float)):  # Check if the attribute is numeric
        plt.hist(values, bins='auto')
    else:  # For non-numeric data, use a bar chart
        from collections import Counter
        counts = Counter(values)
        plt.bar(counts.keys(), counts.values())
        plt.xticks(rotation=90)

    plt.title(f"Distribution of {attr}")
    plt.xlabel(attr)
    plt.ylabel("Frequency")
    plt.tight_layout()
    plt.show()


def plot_comparison(video_lis, video_dic, k):
    """
    Create a plot showing the k most viewed, k most rated, and k most influential videos
    """
    G = create_graph(video_lis, video_dic=video_dic)
    top = pagerank(G, 10, video_dic)

    top_views = sorted(video_lis, key=lambda x: x['views'], reverse=True)[:k]
    top_ratings = sorted(video_lis, key=lambda x: x['ratings'], reverse=True)[:k]

    # Get the details of the top videos from video_dic
    top_influential_videos = [video_dic[vid] for vid in top if vid in video_dic]

    plt.figure()
    plt.yscale('log')

    views_y = [vid['views'] for vid in top_influential_videos]
    ratings_x = [vid['ratings'] for vid in top_influential_videos]
    plt.scatter(ratings_x, views_y, color='red', label='Most Influential', marker='o')

    views_y = [vid['views'] for vid in top_views]
    ratings_x = [vid['ratings'] for vid in top_views]
    plt.scatter(ratings_x, views_y, color='blue', label='Most Viewed', marker='x')

    views_y = [vid['views'] for vid in top_ratings]
    ratings_x = [vid['ratings'] for vid in top_ratings]
    plt.scatter(ratings_x, views_y, color='green', label='Highest Rated', marker='+')

    plt.xlabel('Ratings')
    plt.ylabel('Views')
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    print('Hello Engine')

    all_video_lis, all_video_dic = find_videos()

    print("querying the database for video with id 'OHkEzL4Unck'")
    lis, _ = find_videos(video_id='OHkEzL4Unck');
    print(lis[0])

    print("querying the database for videos in the comedy category")
    lis_comedy, _ = find_videos(category='Comedy')
    print(f"There are {len(lis_comedy)} videos in the comedy category")

    print("querying the database for music videos with more than 100,000 views and likes between [1,000-20,000]")
    lis, _ = find_videos(category='Music', views=(100000, float('inf')), ratings=(1000,20000))
    print(f"There are {len(lis)} videos in that match the previous query")

    print('frequency of comedy videos with ratings in ranges (0,100,500,1000,5000,10000):')
    frequency_by_attr(lis_comedy, 'ratings',[0,100,500,1000,5000,10000])

    print('Frequency plot of comment count of videos with more than 1 million views')
    lis_million, dic_million = find_videos(views=(1000000,float('inf')))
    plot_attribute(lis_million, 'comments')

    print('Frequency plot of categories of videos with more than 1 million views')
    plot_attribute(lis_million, 'category')

    print('Create subnetwork of videos with over a million views')
    G = create_graph(lis_million, dic_million)

    print('Degree statistics of network')
    degree_info(G)

    pagerank(G, 5, all_video_dic)

    #plot_comparison(video_lis, video_dic, 30)
