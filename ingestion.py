from pymongo import MongoClient

# Connect to MongoDB
connection_string = 'REPLACE ME'
client = MongoClient(connection_string)
db = client['YoutubeData']
collection = db['Videos']

# Define the headers as they are not in the file
headers = ['video_id', 'uploader', 'age', 'category', 'length',
           'views', 'rate', 'ratings', 'comments']
paths = ['./0222/0.txt', './0222/1.txt', './0222/2.txt', './0222/3.txt']

# Read and process files
for path in paths:
    print(f'Opening {path}')
    with open(path, 'r') as file:
        count =0
        for line in file:
            # Split the line into parts and extract first 9 fields
            parts = line.strip().split('\t')

            # Skip if there is missing data
            if (len(parts) < 9):
                continue

            data = dict(zip(headers, parts[:9]))

            # Handle the related_ids as a list
            data['related_ids'] = parts[9:]

            # Convert data types
            data['age'] = int(data['age'])
            data['length'] = int(data['length'])
            data['views'] = int(data['views'])
            data['rate'] = float(data['rate'])
            data['ratings'] = int(data['ratings'])
            data['comments'] = int(data['comments'])

            # Insert into MongoDB
            collection.insert_one(data)
            print(f'Added{count}')
            count += 1
