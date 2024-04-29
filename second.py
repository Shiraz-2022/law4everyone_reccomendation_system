from flask import Flask, jsonify
from pymongo import MongoClient
from bson import json_util
import json
import numpy as np
from scipy import spatial
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics.pairwise import euclidean_distances
from sklearn.metrics.pairwise import manhattan_distances

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient('mongodb+srv://shiraz:7TACxQM8U7RQE7ef@law4everyonecluster.mb609.mongodb.net/?retryWrites=true&w=majority')
db = client['test']
blogCollection = db['blogs']
userCollection = db['users']

@app.route('/')
def index():
    return 'Hello, Flask!'

@app.route('/predictBlogs')
def get_blogs():
    try:
        # Fetch blogs from MongoDB with title and description
        blogs = list(blogCollection.find({}, {"title": 1, "description": 1, "tagsProbability": 1}))
        # Fetch users from MongoDB with userName
        users = list(userCollection.find({}, {"userName": 1, "tagsProbability": 1}))

        if blogs:
            blog_info = [{'blog_id': str(blog['_id']), 'title': blog.get('title', ''), 'description': blog.get('description', ''), 'tagsProbability': blog.get('tagsProbability', [])} for blog in blogs]
            user_info = [{'user_id': str(user['_id']), 'userName': user.get('userName', ''), 'tagsProbability': user.get('tagsProbability', [])} for user in users]

            recommended_blogs = {}

            for user_idx, user in enumerate(user_info):
                user_id = user['user_id']
                user_name = user['userName']
                recommended_blogs[user_id] = {'userName': user_name, 'recommendedBlogs': []}

                user_array = np.array(user['tagsProbability']).reshape(1, -1)
                for blog_idx, blog in enumerate(blog_info):
                    blog_id = blog['blog_id']
                    title = blog['title']
                    description = blog['description']
                    blog_array = np.array(blog['tagsProbability']).reshape(1, -1)
                    
                    # Calculate cosine similarity
                    cosine_sim = cosine_similarity(user_array, blog_array)[0][0]
                    # Calculate euclidean distance
                    euclidean_dist = euclidean_distances(user_array, blog_array)[0][0]
                    # Calculate manhattan distance
                    manhattan_dist = manhattan_distances(user_array, blog_array)[0][0]

                    # You can adjust thresholds or combine different methods for better recommendations
                    if cosine_sim > 0.4 or euclidean_dist < 0.5 or manhattan_dist < 0.5:
                        recommended_blogs[user_id]['recommendedBlogs'].append({'blog_id': blog_id, 'title': title, 'description': description})

            return jsonify(recommended_blogs)
        else:
            return jsonify({'message': 'No blogs found'})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
